from mona_sdk.auth.auth_requests import BASIC_HEADER
from mona_sdk.auth.auth_utils import (
    API_KEYS_TO_TOKEN_DATA,
    get_current_token_by_api_key,
)
from mona_sdk.auth.auth_globals import (
    MANUAL_TOKEN_STRING_FOR_API_INTERNAL_KEY,
    IS_AUTHENTICATED_INTERNAL_KEY,
    MANUAL_ACCESS_TOKEN_KEY,
)
from mona_sdk.auth.auth_classes.base_auth import Base
from mona_sdk.client_exceptions import MonaInitializationException
from mona_sdk.logger import get_logger


class ManualTokenAuth(Base):
    def __init__(self, user_id, *args, **kwargs):
        super().__init__(*args, user_id=user_id, **kwargs)
        self.api_key = MANUAL_TOKEN_STRING_FOR_API_INTERNAL_KEY

    def _raise_if_missing_params(self):
        if not self.user_id:
            raise MonaInitializationException(
                f"Mona Client is initiated with an auth mode that requires user_id."
            )

        if (
            not self.override_rest_api_host
            and not self.override_rest_api_full_url
            and not self.override_app_server_host
            and not self.override_app_server_full_url
        ):
            raise MonaInitializationException(
                "Mona client is initiated with an "
                "auth mode the requires a host or a "
                "full url."
            )

    def initial_auth(self):
        get_logger().info("Manual token mode is on.")

        API_KEYS_TO_TOKEN_DATA[MANUAL_TOKEN_STRING_FOR_API_INTERNAL_KEY] = {
            MANUAL_ACCESS_TOKEN_KEY: self.access_token,
            IS_AUTHENTICATED_INTERNAL_KEY: True,
        }

        return True

    def is_authenticated(self):
        return True

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
