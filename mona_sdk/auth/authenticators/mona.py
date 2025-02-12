import jwt
import requests
from mona_sdk.auth.utils import get_token_info_by_api_key, get_current_token_by_api_key
from mona_sdk.auth.globals import (
    BASIC_HEADER,
    EXPIRES_KEY_IN_MONA,
    MONA_ACCESS_TOKEN_KEY,
    MONA_REFRESH_TOKEN_KEY,
)
from mona_sdk.auth.authenticators.base_authenticator import BaseAuthenticator


class MonaAuth(BaseAuthenticator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.expires_key = EXPIRES_KEY_IN_MONA

    def _raise_if_missing_params(self):
        self._raise_if_missing_token_params()

    def request_access_token(self):
        return requests.request(
            "POST",
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
            json={
                MONA_REFRESH_TOKEN_KEY: get_token_info_by_api_key(
                    self.api_key, MONA_REFRESH_TOKEN_KEY
                )
            },
        )

    def get_auth_header(self):
        token = get_current_token_by_api_key(
            api_key=self.api_key, access_token_key=MONA_ACCESS_TOKEN_KEY
        )

        return BaseAuthenticator.create_auth_headers(token)
