from mona_sdk.logger import get_logger
from mona_sdk.auth.utils import (
    API_KEYS_TO_TOKEN_DATA,
    get_current_token_by_api_key,
)
from mona_sdk.auth.globals import (
    MANUAL_ACCESS_TOKEN_KEY,
    IS_AUTHENTICATED_INTERNAL_KEY,
    MANUAL_TOKEN_STRING_FOR_API_INTERNAL_KEY,
    BASIC_HEADER,
)
from mona_sdk.client_exceptions import MonaInitializationException
from mona_sdk.auth.authenticators.base import Base


class ManualTokenAuth(Base):
    def __init__(self, user_id, *args, **kwargs):
        super().__init__(*args, user_id=user_id, **kwargs)
        self.api_key = MANUAL_TOKEN_STRING_FOR_API_INTERNAL_KEY

    def initial_auth(self):
        get_logger().info("Manual token mode is on.")

        API_KEYS_TO_TOKEN_DATA[MANUAL_TOKEN_STRING_FOR_API_INTERNAL_KEY] = {
            MANUAL_ACCESS_TOKEN_KEY: self.access_token,
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

        return {
            **BASIC_HEADER,
            "Authorization": f"Bearer {token}",
        }
