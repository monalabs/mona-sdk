from abc import abstractmethod

from mona_sdk.auth import (
    authentication_lock,
    API_KEYS_TO_TOKEN_DATA,
    _calculate_time_to_refresh,
    handle_authentications_error,
    _get_error_string_from_token_info,
    _get_auth_response_with_retries,
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
        access_token=None,
    ):
        self.api_key = api_key
        self.secret = secret
        self.num_of_retries = num_of_retries_for_authentication
        self.auth_wait_time_sec = wait_time_for_authentication_retries
        self.raise_auth_exceptions = raise_authentication_exceptions
        self.access_token=access_token

        # Will be overwritten in the child which are going to use this property.
        self.expires_key = None

    def initial_auth(self):
        if not self.is_authenticated(self.api_key):
            # Make sure only one instance of the client (with the given api_key) can get a
            # new token. That token will be shared between all instances that share an
            # api_key.

            # todo figure out where are we brining this from.
            with authentication_lock:
                # The inner check is needed to avoid multiple redundant authentications.
                # todo what about making this private?
                # todo what about moving this file from places?
                if not self.is_authenticated(self.api_key):

                    # todo we need to work on this function here.
                    response = self._request_access_token_with_retries(
                        # todo make sure all of those pass here.
                        self.api_key,
                        self.secret,
                        self.num_of_retries,
                        self.auth_wait_time_sec,
                    )
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

        if self.is_authenticated(self.api_key):
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

    # todo maybe this should allow by default?
    @abstractmethod
    def is_authenticated(self, _):
        pass

    @abstractmethod
    def should_refresh_token(_):
        pass

    # todo interesting how to implement this
    @abstractmethod
    def refresh_token(_):
        pass

    @abstractmethod
    def request_access_token(self):
        pass

    def _request_access_token_with_retries(
        self, api_key, secret, num_of_retries, auth_wait_time_sec
    ):
        return _get_auth_response_with_retries(
            lambda: self.request_access_token(),
            num_of_retries=num_of_retries,
            # todo make sure we are talking about seconds here
            auth_wait_time_sec=auth_wait_time_sec,
        )
