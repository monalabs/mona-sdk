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

from logger import get_logger
from auth_consts import (
    ERRORS,
    ACCESS_TOKEN,
    REFRESH_TOKEN,
    EXPIRED_IN_OIDC,
    TIME_TO_REFRESH,
    IS_AUTHENTICATED,
    EXPIRES_IN_FRONTEGG,
    MANUAL_TOKEN_STRING_FOR_API_KEY,
)
from client_util import get_dict_result
from auth_requests import (
    BASIC_HEADER,
    _request_access_token_once,
    _request_refresh_token_once,
)
from requests.models import Response
from client_exceptions import MonaAuthenticationException
from auth_master_swithces import FRONTEGG_AUTH_MODE, USE_REFRESH_TOKENS

# A new token expires after 22 hours, REFRESH_TOKEN_SAFETY_MARGIN is the safety gap of
# time to refresh the token before it expires (i.e. - in case
# REFRESH_TOKEN_SAFETY_MARGIN = 2, and the token is about to expire in 2 hours or less,
# the client will automatically refresh the token to a new one).
REFRESH_TOKEN_SAFETY_MARGIN = datetime.timedelta(
    hours=int(os.environ.get("MONA_SDK_REFRESH_TOKEN_SAFETY_MARGIN", 2))
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


def initial_authentication(mona_client):
    if mona_client.get_manual_access_token():
        get_logger().info("Manual token provided.")

        API_KEYS_TO_TOKEN_DATA[MANUAL_TOKEN_STRING_FOR_API_KEY] = {
            ACCESS_TOKEN: mona_client.get_manual_access_token(),
            IS_AUTHENTICATED: True,
        }
        return True

    if not is_authenticated(mona_client.api_key):
        # Make sure only one instance of the client (with the given api_key) can get a
        # new token. That token will be shared between all instances that share an
        # api_key.
        with authentication_lock:
            # The inner check is needed to avoid multiple redundant authentications.
            if not is_authenticated(mona_client.api_key):
                response = _request_access_token_with_retries(mona_client)
                API_KEYS_TO_TOKEN_DATA[mona_client.api_key] = response.json()

                # response.ok will be True if authentication was successful and
                # false if not.
                API_KEYS_TO_TOKEN_DATA[mona_client.api_key][
                    IS_AUTHENTICATED
                ] = response.ok

                time_to_refresh = _calculate_time_to_refresh(mona_client.api_key)
                if time_to_refresh:
                    API_KEYS_TO_TOKEN_DATA[mona_client.api_key][
                        TIME_TO_REFRESH
                    ] = time_to_refresh

    if is_authenticated(mona_client.api_key):
        # Success
        get_logger().info(
            f"New client token info: {API_KEYS_TO_TOKEN_DATA[mona_client.api_key]}"
        )
        return True

    else:
        # Failure
        return _handle_authentications_error(
            f"Mona's client could not authenticate. "
            f"errors: {_get_error_string_from_token_info(mona_client.api_key)}",
            mona_client.raise_authentication_exceptions,
        )


def _get_error_string_from_token_info(api_key):
    error_list = _get_token_info_by_api_key(api_key, ERRORS)
    return ", ".join(_get_token_info_by_api_key(api_key, ERRORS)) if error_list else ""


def _request_access_token_with_retries(mona_client):
    return _get_auth_response_with_retries(
        lambda: _request_access_token_once(
            mona_client.api_key, mona_client.secret, mona_client.oidc_scope
        ),
        num_of_retries=mona_client.num_of_retries_for_authentication,
        auth_wait_time_sec=mona_client.wait_time_for_authentication_retries,
    )


def _request_refresh_token_with_retries(refresh_token_key, mona_client):
    return _get_auth_response_with_retries(
        lambda: _request_refresh_token_once(refresh_token_key),
        num_of_retries=mona_client.num_of_retries_for_authentication,
        auth_wait_time_sec=mona_client.wait_time_for_authentication_retries,
    )


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
    for i in range(num_of_retries + 1):
        try:
            response = response_generator()
            # Check that response is json-serializable.
            response.json()
            # Got a response, log and break the retry loop.
            get_logger().info(f"Got an authentication response after {i} retries.")
            break

        except Exception:
            if i == num_of_retries:
                # Retried to authenticate num_of_retries times and failed due to
                # authentications server problems, return a response with the relevant
                # info.
                response = _create_a_bad_response(
                    '{"errors": ["Could not connect to authentication server",'
                    ' "Number of retries: ' + str(i) + '"]}'
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
    return _get_token_info_by_api_key(api_key, ACCESS_TOKEN)


def _get_token_info_by_api_key(api_key, token_data_arg):
    """
    Returns the value of the wanted data for the given api_key.
    Returns None if the api_key or the arg does not exist.
    """
    return API_KEYS_TO_TOKEN_DATA.get(api_key, {}).get(token_data_arg)


def is_authenticated(api_key):
    """
    :return: True if Mona's client holds a valid token and can communicate with Mona's
    servers (or can refresh the token in order to), False otherwise.
    """
    return _get_token_info_by_api_key(api_key, IS_AUTHENTICATED)


def _calculate_time_to_refresh(api_key):
    """
    Calculates the time the access token needs to be refreshed and updates the relevant
    api_key token data.
    """
    if not is_authenticated(api_key):
        return None

    token_expires = datetime.datetime.now() + datetime.timedelta(
        seconds=_get_token_info_by_api_key(
            api_key,
            token_data_arg=EXPIRES_IN_FRONTEGG
            if FRONTEGG_AUTH_MODE
            else EXPIRED_IN_OIDC,
        )
    )

    return token_expires - REFRESH_TOKEN_SAFETY_MARGIN


def _handle_authentications_error(
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


def _should_refresh_token(mona_client):
    """
    :return: True if the token has expired, or is about to expire in
    REFRESH_TOKEN_SAFETY_MARGIN hours or less, False otherwise.
    """

    # We don't know when the manual token is going to expire, therefore we'll let the
    # user use it until she'll start getting authentication errors from the BE.
    if mona_client.get_manual_access_token():
        get_logger().info("Not refreshing manual token")
        return False

    return (
        _get_token_info_by_api_key(mona_client.api_key, TIME_TO_REFRESH)
        < datetime.datetime.now()
    )


def _get_refresh_token_with_fallback(mona_client):

    # TODO(elie): Support refresh tokens for OIDC.
    if not USE_REFRESH_TOKENS:
        return _request_access_token_with_retries(mona_client)

    refresh_token_key = _get_token_info_by_api_key(mona_client.api_key, REFRESH_TOKEN)
    response = _request_refresh_token_with_retries(refresh_token_key, mona_client)

    if not response.ok:
        get_logger().warning(
            f"Failed to refresh the access token, trying to get a new one. "
            f"{response.text}"
        )

        # Fall back to regular access tokens
        response = _request_access_token_with_retries(mona_client)

    return response


def _refresh_token(mona_client):
    """
    Gets a new token and sets the needed fields.
    """

    response = _get_refresh_token_with_fallback(mona_client)

    # The current client token info will not change if the response was bad, so that on
    # the next function call the client will try to refresh the token again.
    if not response.ok:
        return response

    # Update the client's new token info.
    API_KEYS_TO_TOKEN_DATA[mona_client.api_key] = response.json()

    API_KEYS_TO_TOKEN_DATA[mona_client.api_key][IS_AUTHENTICATED] = True

    time_to_refresh = _calculate_time_to_refresh(mona_client.api_key)

    if time_to_refresh:
        API_KEYS_TO_TOKEN_DATA[mona_client.api_key][TIME_TO_REFRESH] = time_to_refresh

    get_logger().info(
        f"Refreshed access token, the new token info:"
        f" {API_KEYS_TO_TOKEN_DATA[mona_client.api_key]}"
    )

    return response


def get_auth_header(api_key, with_auth):
    return (
        {
            **BASIC_HEADER,
            "Authorization": f"Bearer {get_current_token_by_api_key(api_key)}",
        }
        if with_auth
        else BASIC_HEADER
    )
