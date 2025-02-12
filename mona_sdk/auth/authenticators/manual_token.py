from mona_sdk.logger import get_logger
from mona_sdk.auth.utils import API_KEYS_TO_TOKEN_DATA, get_current_token_by_api_key
from mona_sdk.auth.globals import (
    MANUAL_ACCESS_TOKEN_KEY,
    IS_AUTHENTICATED_INTERNAL_KEY,
    MANUAL_TOKEN_STRING_FOR_API_INTERNAL_KEY,
)
from mona_sdk.client_exceptions import MonaInitializationException
from mona_sdk.auth.authenticators.base_authenticator import BaseAuthenticator


class ManualTokenAuth(BaseAuthenticator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key = MANUAL_TOKEN_STRING_FOR_API_INTERNAL_KEY

    def _raise_if_missing_manual_token(self):
        if not self.manual_access_token:
            raise MonaInitializationException(
                "MonaAuth is initiated with missing params. "
                "Please provide access_token."
            )

    def _raise_if_missing_params(self):
        self._raise_if_missing_manual_token()
        self._raise_if_missing_user_id()
        self._raise_if_missing_backend_params()

    def initial_auth(self):
        get_logger().info("Manual token mode is on.")

        API_KEYS_TO_TOKEN_DATA[MANUAL_TOKEN_STRING_FOR_API_INTERNAL_KEY] = {
            MANUAL_ACCESS_TOKEN_KEY: self.manual_access_token,
            IS_AUTHENTICATED_INTERNAL_KEY: True,
        }

        return True

    def is_authenticated(self):
        return True

    def request_access_token(self):
        raise NotImplementedError

    def request_refresh_token(self):
        raise NotImplementedError

    def should_refresh_token(self):
        return False

    def get_auth_header(self):
        token = get_current_token_by_api_key(
            api_key=self.api_key, access_token_key=MANUAL_ACCESS_TOKEN_KEY
        )

        return BaseAuthenticator.create_auth_headers(token)
