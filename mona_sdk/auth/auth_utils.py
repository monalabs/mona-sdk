# ----------------------------------------------------------------------------
#    Copyright 2021 MonaLabs.io
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
# ----------------------------------------------------------------------------
"""
This module holds all authentication information and related functions. For a given
api_key, it can provide a new access token, refresh an expired access token or give
authentication status information.
"""
import os
import time
import datetime
from threading import Lock

from mona_sdk.logger import get_logger
from requests.models import Response
from mona_sdk.client_util import get_dict_result
from mona_sdk.auth.auth_globals import (
    ERRORS,
    ACCESS_TOKEN,
    TIME_TO_REFRESH_INTERNAL_KEY,
    IS_AUTHENTICATED,
    SHOULD_USE_NO_AUTH_MODE,
    SHOULD_USE_REFRESH_TOKENS,
)
from mona_sdk.auth.auth_requests import (
    BASIC_HEADER,
)
from mona_sdk.client_exceptions import MonaAuthenticationException

# As of 29/1/2025, a new token expires after 4 hours. REFRESH_TOKEN_SAFETY_MARGIN is the
# safety gap of time to refresh the token before it expires (i.e. - in case
# REFRESH_TOKEN_SAFETY_MARGIN = 2, and the token is about to expire in 2 hours or less,
# the client will automatically refresh the token to a new one).
REFRESH_TOKEN_SAFETY_MARGIN_HOURS = datetime.timedelta(
    minutes=int(
        os.environ.get(
            "MONA_SDK_REFRESH_TOKEN_SAFETY_MARGIN_HOURS",
            # Backward compatibility.
            os.environ.get("MONA_SDK_REFRESH_TOKEN_SAFETY_MARGIN", 0.5),
        )
    )
)

OIDC_CLIENT_ID = os.environ.get("MONA_SDK_OIDC_CLIENT_ID")
OIDC_CLIENT_SECRET = os.environ.get("MONA_SDK_OIDC_CLIENT_SECRET")
OIDC_SCOPE = os.environ.get("MONA_SDK_OIDC_SCOPE")

# This dict maps between every api_key (each api_key is saved only once in this dict)
# and its access token info (if the given api_key is authenticated it will contain the
# token itself, its expiration date and the key to refresh it, otherwise it will contain
# the errors that occurred while trying to authenticate).
API_KEYS_TO_TOKEN_DATA = {}

# TODO(anat): Consider initializing a different lock for each api_key.
authentication_lock = Lock()


def _get_error_string_from_token_info(api_key):
    error_list = get_token_info_by_api_key(api_key, ERRORS)
    return ", ".join(get_token_info_by_api_key(api_key, ERRORS)) if error_list else ""


# todo currently refactoring this guy.
# todo don't think that we should use the scope here




def _get_auth_response_with_retries(
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
                    '{"errors": ["Could not connect to authentication server",'
                    ' "Number of retries: ' + str(i) + '"]}'
                    ' "Exception: ' + str(e) + '"'
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


def get_current_token_by_api_key(api_key):
    """
    :return: The given api_key's current access token.
    """
    return get_token_info_by_api_key(api_key, ACCESS_TOKEN)


def get_token_info_by_api_key(api_key, token_data_arg):
    """
    Returns the value of the wanted data for the given api_key.
    Returns None if the api_key or the arg does not exist.
    """
    return API_KEYS_TO_TOKEN_DATA.get(api_key, {}).get(token_data_arg)


# todo so we'll remove this soon?
def is_authenticated(api_key):
    """
    :return: True if Mona's client holds a valid token and can communicate with Mona's
    servers (or can refresh the token in order to), False otherwise.
    """
    return get_token_info_by_api_key(api_key, IS_AUTHENTICATED)


# todo this is general auth - make sure that others also make sense here
def _calculate_time_to_refresh(api_key, expires_key):
    """
    Calculates the time the access token needs to be refreshed and updates the relevant
    api_key token data.
    """
    if not is_authenticated(api_key):
        return None

    token_expires = datetime.datetime.now() + datetime.timedelta(
        seconds=get_token_info_by_api_key(
            api_key,
            token_data_arg=expires_key,
        )
    )

    return token_expires - REFRESH_TOKEN_SAFETY_MARGIN_HOURS


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







def get_auth_header(api_key):

    return (
        BASIC_HEADER
        if SHOULD_USE_NO_AUTH_MODE
        else {
            **BASIC_HEADER,
            "Authorization": f"Bearer {get_current_token_by_api_key(api_key)}",
        }
    )
