import datetime

import jwt
import requests

from mona_sdk.auth.auth_utils import (
    get_current_token_by_api_key,
    get_token_info_by_api_key,
)
from mona_sdk.auth.auth_globals import (
    EXPIRES_KEY_IN_MONA,
    REFRESH_TOKEN_KEY,
    SHOULD_USE_REFRESH_TOKENS,
    TIME_TO_REFRESH_INTERNAL_KEY,
    MONA_ACCESS_TOKEN_KEY,
)
from mona_sdk.auth.auth_requests import BASIC_HEADER
from mona_sdk.auth.auth_classes.base_auth import Base
from mona_sdk.client_exceptions import MonaInitializationException
from mona_sdk.logger import get_logger


class MonaAuth(Base):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.expires_key = EXPIRES_KEY_IN_MONA

    def _raise_if_missing_params(self):
        if not self.auth_api_token_url or not self.api_key or not self.secret:
            raise MonaInitializationException(
                "MonaAuth is initiated with missing params. "
                "Please provide auth_api_token_url, api_key and secret."
            )

    def request_access_token(self):
        return requests.request(
            "POST",
            # todo just make sure that we the correct value here
            self.auth_api_token_url,
            headers=BASIC_HEADER,
            json={"clientId": self.api_key, "secret": self.secret},
        )

    def get_user_id(self):
        """
        :return: The customer's user id (tenant id).
        """
        decoded_token = jwt.decode(
            get_current_token_by_api_key(self.api_key, MONA_ACCESS_TOKEN_KEY),
            verify=False,
            options={"verify_signature": False},
        )
        return decoded_token["tenantId"]

    def request_refresh_token(self):
        """
        Sends a refresh token REST request and returns the response.
        """
        return requests.request(
            "POST",
            self.refresh_token_url,
            headers=BASIC_HEADER,
            # todo what is this weird usage of a dict all over the place
            json={
                "refreshToken": get_token_info_by_api_key(
                    self.api_key, REFRESH_TOKEN_KEY
                )
            },
        )

    def get_auth_header(self):
        token = get_current_token_by_api_key(
            api_key=self.api_key, access_token_key=MONA_ACCESS_TOKEN_KEY
        )

        return {
            **BASIC_HEADER,
            "Authorization": f"Bearer {token}",
        }
