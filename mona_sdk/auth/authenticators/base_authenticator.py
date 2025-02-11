from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from mona_sdk.logger import get_logger
from mona_sdk.auth.utils import (
    API_KEYS_TO_TOKEN_DATA,
    authentication_lock,
    get_token_info_by_api_key,
    handle_authentications_error,
    get_auth_response_with_retries,
    get_error_string_from_token_info,
)
from mona_sdk.auth.globals import (
    BASIC_HEADER,
    REFRESH_TOKEN_SAFETY_MARGIN,
    TIME_TO_REFRESH_INTERNAL_KEY,
    IS_AUTHENTICATED_INTERNAL_KEY,
)
from mona_sdk.client_exceptions import MonaInitializationException


class BaseAuthenticator(ABC):
    def __init__(
        self,
        api_key,
        secret,
        num_of_retries_for_authentication,
        wait_time_for_authentication_retries,
        raise_authentication_exceptions,
        auth_api_token_url=None,
        refresh_token_url=None,
        access_token=None,
        user_id=None,
        override_app_server_host=None,
        override_app_server_full_url=None,
        override_rest_api_host=None,
        override_rest_api_full_url=None,
        should_use_refresh_tokens=False,
    ):
        self.api_key = api_key
        self.secret = secret
        self.num_of_retries = num_of_retries_for_authentication
        self.auth_wait_time_sec = wait_time_for_authentication_retries
        self.raise_auth_exceptions = raise_authentication_exceptions
        self.manual_access_token = access_token
        self.user_id = user_id
        self.override_app_server_host = override_app_server_host
        self.override_app_server_full_url = override_app_server_full_url
        self.override_rest_api_host = override_rest_api_host
        self.override_rest_api_full_url = override_rest_api_full_url
        self.auth_api_token_url = auth_api_token_url
        self.refresh_token_url = refresh_token_url
        self.should_use_refresh_tokens = should_use_refresh_tokens

        # Will be overwritten in the child which are going to use this property.
        self.expires_key = None

        self._raise_if_missing_params()

    @classmethod
    def get_valid_keys(cls):
        return [
            "api_key",
            "secret",
            "num_of_retries_for_authentication",
            "wait_time_for_authentication_retries",
            "raise_authentication_exceptions",
            "auth_api_token_url",
            "refresh_token_url",
            "access_token",
            "user_id",
            "override_app_server_host",
            "override_app_server_full_url",
            "override_rest_api_host",
            "override_rest_api_full_url",
            "should_use_refresh_tokens",
        ]

    def _raise_if_missing_params(self):
        self._raise_if_missing_user_id()
        self._raise_if_missing_backend_params()

    def _raise_if_missing_user_id(self):
        if not self.user_id:
            raise MonaInitializationException(
                f"Mona Client is initiated with an auth mode that requires user_id."
            )

    def _raise_if_missing_backend_params(self):
        if not any(
            [
                self.override_rest_api_host,
                self.override_rest_api_full_url,
                self.override_app_server_host,
                self.override_app_server_full_url,
            ]
        ):
            raise MonaInitializationException(
                "Mona client is initiated with an "
                "auth mode the requires a host or a "
                "full url."
            )

    def _raise_if_missing_token_params(self):
        if not self.auth_api_token_url or not self.api_key or not self.secret:
            raise MonaInitializationException(
                "MonaAuth is initiated with missing params. "
                "Please provide auth_api_token_url, api_key and secret."
            )

    def initial_auth(self):
        if not self.is_authenticated():
            # Make sure only one instance of the client (with the given api_key) can get
            # a new token. That token will be shared between all instances that share
            # an api_key.

            with authentication_lock:
                # The inner check is needed to avoid multiple redundant authentications.
                if not self.is_authenticated():

                    response = self._request_access_token_with_retries()
                    API_KEYS_TO_TOKEN_DATA[self.api_key] = response.json()

                    # response.ok will be True if authentication was successful and
                    # false if not.
                    API_KEYS_TO_TOKEN_DATA[self.api_key][
                        IS_AUTHENTICATED_INTERNAL_KEY
                    ] = response.ok

                    time_to_refresh = self.calculate_time_to_refresh()
                    if time_to_refresh:
                        API_KEYS_TO_TOKEN_DATA[self.api_key][
                            TIME_TO_REFRESH_INTERNAL_KEY
                        ] = time_to_refresh

        if self.is_authenticated():
            # Success
            get_logger().info(
                f"New client token info: {API_KEYS_TO_TOKEN_DATA[self.api_key]}"
            )
            return True

        else:
            # Failure
            return handle_authentications_error(
                f"Mona's client could not authenticate. "
                f"errors: {get_error_string_from_token_info(self.api_key)}",
                should_raise_exception=self.raise_auth_exceptions,
            )

    def is_authenticated(self):
        return get_token_info_by_api_key(self.api_key, IS_AUTHENTICATED_INTERNAL_KEY)

    @abstractmethod
    def request_access_token(self):
        pass

    @abstractmethod
    def request_refresh_token(self):
        pass

    def _request_access_token_with_retries(self):
        return get_auth_response_with_retries(
            lambda: self.request_access_token(),
            num_of_retries=self.num_of_retries,
            auth_wait_time_sec=self.auth_wait_time_sec,
        )

    def _request_refresh_token_with_retries(self):
        return get_auth_response_with_retries(
            lambda: self.request_refresh_token(),
            num_of_retries=self.num_of_retries,
            auth_wait_time_sec=self.auth_wait_time_sec,
        )

    def refresh_token(self):
        """
        Gets a new token and sets the needed fields.
        """

        response = self._get_refresh_token_with_fallback()

        # The current client token info will not change if the response was bad, so that on
        # the next function call the client will try to refresh the token again.
        if not response.ok:
            return response

        # Update the client's new token info.
        API_KEYS_TO_TOKEN_DATA[self.api_key] = response.json()

        API_KEYS_TO_TOKEN_DATA[self.api_key][IS_AUTHENTICATED_INTERNAL_KEY] = True

        time_to_refresh = self.calculate_time_to_refresh()

        if time_to_refresh:
            API_KEYS_TO_TOKEN_DATA[self.api_key][
                TIME_TO_REFRESH_INTERNAL_KEY
            ] = time_to_refresh

        get_logger().info(
            f"Refreshed access token, the new token info:"
            f" {API_KEYS_TO_TOKEN_DATA[self.api_key]}"
        )

        return response

    def _get_refresh_token_with_fallback(self):

        if not self.should_use_refresh_tokens:
            return self._request_access_token_with_retries()

        response = self._request_refresh_token_with_retries()

        if not response.ok:
            get_logger().warning(
                f"Failed to refresh the access token, trying to get a new one. "
                f"{response.text}"
            )

            # Fall back to regular access tokens
            response = self._request_access_token_with_retries()

        return response

    def should_refresh_token(self):
        time_to_refresh = get_token_info_by_api_key(
            self.api_key, TIME_TO_REFRESH_INTERNAL_KEY
        )

        if not time_to_refresh:
            get_logger().warning("No time to refresh found, refreshing token.")
            return True

        return time_to_refresh < datetime.now()

    @staticmethod
    def create_auth_headers(token=None):
        return (
            {**BASIC_HEADER}
            if not token
            else {
                **BASIC_HEADER,
                "Authorization": f"Bearer {token}",
            }
        )

    def get_auth_header(self):
        return BaseAuthenticator.create_auth_headers()

    def calculate_time_to_refresh(self):
        """
        Calculates the time the access token needs to be refreshed and updates the
        relevant api_key token data.
        """
        if not self.is_authenticated():
            return None

        token_expires = datetime.now() + timedelta(
            seconds=get_token_info_by_api_key(
                self.api_key,
                token_data_arg=self.expires_key,
            )
        )

        return token_expires - REFRESH_TOKEN_SAFETY_MARGIN

    @staticmethod
    def get_unauthenticated_mode_error_message():
        """
        If we are in AUTH_MODE="NO_AUTH", return an error message (suggesting
        that auth being off might be the cause for the exception)
        and an empty string otherwise.
        """
        return ""

    def is_authentication_used(self):
        return True
