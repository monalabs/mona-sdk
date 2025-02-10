"""
This module holds all authentication information and related functions. For a given
api_key, it can provide a new access token, refresh an expired access token or give
authentication status information.
"""
import time
from threading import Lock

from mona_sdk.logger import get_logger
from requests.models import Response
from mona_sdk.client_util import get_dict_result
from mona_sdk.auth.globals import ERRORS_INTERNAL_KEY
from mona_sdk.client_exceptions import MonaAuthenticationException

# This dict maps between every api_key (each api_key is saved only once in this dict)
# and its access token info (if the given api_key is authenticated it will contain the
# token itself, its expiration date and the key to refresh it, otherwise it will contain
# the errors that occurred while trying to authenticate).
API_KEYS_TO_TOKEN_DATA = {}

# TODO(anat): Consider initializing a different lock for each api_key.
authentication_lock = Lock()


def get_error_string_from_token_info(api_key):
    error_list = get_token_info_by_api_key(api_key, ERRORS_INTERNAL_KEY)
    return (
        ", ".join(get_token_info_by_api_key(api_key, ERRORS_INTERNAL_KEY))
        if error_list
        else ""
    )


def get_auth_response_with_retries(
    response_generator,
    num_of_retries,
    auth_wait_time_sec,
):
    """
    Sends an authentication request (first time/refresh) with a retry mechanism.
    :param: response_generator (lambda)
            A function call that sends the wanted REST request.
    :return: The response received from the authentication server.
    """
    response = None

    for i in range(num_of_retries + 1):
        try:
            response = response_generator()
            # Check that response is json-serializable.
            response.json()
            # Got a response, log and break the retry loop.
            get_logger().info(f"Got an authentication response after {i} retries.")
            break

        except Exception as e:
            if i == num_of_retries:
                # Retried to authenticate num_of_retries times and failed due to
                # authentications server problems, return a response with the relevant
                # info.
                response = _create_a_bad_response(
                    f'{{"errors": ["Could not connect to authentication server", '
                    f'"Number of retries: {i}"]}} "Exception: {e}"'
                )

            else:
                # TODO(anat): Support exponential growth in wait times between retries.
                # Has more retries, sleep before trying again.
                time.sleep(auth_wait_time_sec)

    return response


def _create_a_bad_response(content):
    """
    :param: content (str)
            The content of the response.
    :return: A functioning bad REST response instance with the given content.
    """
    response = Response()
    response.status_code = 400
    if type(content) is str:
        # _content expect bytes.
        response._content = bytes(content, "utf8")

    return response


def get_current_token_by_api_key(api_key, access_token_key):
    """
    :return: The given api_key's current access token.
    """
    return get_token_info_by_api_key(api_key, access_token_key)


def get_token_info_by_api_key(api_key, token_data_arg):
    """
    Returns the value of the wanted data for the given api_key.
    Returns None if the api_key or the arg does not exist.
    """
    return API_KEYS_TO_TOKEN_DATA.get(api_key, {}).get(token_data_arg)


def handle_authentications_error(
    error_message, should_raise_exception, message_to_log=None
):
    """
    Logs an error and raises MonaAuthenticationException if
    RAISE_AUTHENTICATION_EXCEPTIONS is true, else returns false.
    """
    get_logger().error(error_message)

    if message_to_log:
        get_logger().error(f"Failed to send the following to mona: {message_to_log}")

    if should_raise_exception:
        raise MonaAuthenticationException(error_message)

    return get_dict_result(False, None, error_message)
