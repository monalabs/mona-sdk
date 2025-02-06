from abc import abstractmethod

from mona_sdk.auth import (
    authentication_lock,
    API_KEYS_TO_TOKEN_DATA,
    _calculate_time_to_refresh,
    handle_authentications_error,
    _get_error_string_from_token_info,
    _get_auth_response_with_retries,
    get_token_info_by_api_key,
)
from mona_sdk.auth_globals import IS_AUTHENTICATED, TIME_TO_REFRESH
from mona_sdk.logger import get_logger


class Base:
    def __init__(
        self,
        api_key,
        secret,
        num_of_retries_for_authentication,
        wait_time_for_authentication_retries,
        raise_authentication_exceptions,
        auth_api_token_url=None,
        access_token=None,
        user_id=None,
        override_app_server_host=None,
        override_app_server_full_url=None,
        override_rest_api_host=None,
        override_rest_api_full_url=None,
    ):
        self.api_key = api_key
        self.secret = secret
        self.num_of_retries = num_of_retries_for_authentication
        self.auth_wait_time_sec = wait_time_for_authentication_retries
        self.raise_auth_exceptions = raise_authentication_exceptions
        self.access_token = access_token
        self.user_id = user_id
        self.override_app_server_host = override_app_server_host
        self.override_app_server_full_url = override_app_server_full_url
        self.override_rest_api_host = override_rest_api_host
        self.override_rest_api_full_url = override_rest_api_full_url
        self.auth_api_token_url = auth_api_token_url

        # Will be overwritten in the child which are going to use this property.
        self.expires_key = None
        self._raise_if_missing_params()

    @abstractmethod
    def _raise_if_missing_params(self):
        pass

    def initial_auth(self):
        if not self.is_authenticated():
            # Make sure only one instance of the client (with the given api_key) can get a
            # new token. That token will be shared between all instances that share an
            # api_key.

            # todo figure out where are we brining this from.
            with authentication_lock:
                # The inner check is needed to avoid multiple redundant authentications.
                # todo what about making this private?
                # todo what about moving this file from places?
                if not self.is_authenticated():

                    # todo we need to work on this function here.
                    response = self._request_access_token_with_retries()
                    API_KEYS_TO_TOKEN_DATA[self.api_key] = response.json()

                    # response.ok will be True if authentication was successful and
                    # false if not.
                    API_KEYS_TO_TOKEN_DATA[self.api_key][IS_AUTHENTICATED] = response.ok

                    time_to_refresh = _calculate_time_to_refresh(
                        # todo not sure how we should treat this.
                        self.api_key,
                        expires_key=self.expires_key,
                    )
                    if time_to_refresh:
                        API_KEYS_TO_TOKEN_DATA[self.api_key][
                            TIME_TO_REFRESH
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
                f"errors: {_get_error_string_from_token_info(self.api_key)}",
                # todo make sure that this is passed like it should.
                should_raise_exception=self.raise_auth_exceptions,
            )

    # todo when we use strings  there, we might lose some ability
    #   think about that./
    def is_authenticated(self):
        return get_token_info_by_api_key(self.api_key, IS_AUTHENTICATED)

    def request_access_token(self):
        pass

    def _request_access_token_with_retries(self):
        return _get_auth_response_with_retries(
            lambda: self.request_access_token(),
            num_of_retries=self.num_of_retries,
            auth_wait_time_sec=self.auth_wait_time_sec,
        )
