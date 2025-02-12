import requests
from mona_sdk.auth.utils import get_current_token_by_api_key
from mona_sdk.auth.globals import (
    URL_ENCODED_HEADER,
    EXPIRES_KEY_IN_OIDC,
    OIDC_ACCESS_TOKEN_KEY,
    CLIENT_CREDENTIALS_GRANT_TYPE,
)
from mona_sdk.client_exceptions import MonaInitializationException
from mona_sdk.auth.authenticators.base_authenticator import BaseAuthenticator


class OidcAuth(BaseAuthenticator):
    def __init__(self, *args, api_key, oidc_scope=None, **kwargs):
        super().__init__(*args, api_key, **kwargs)
        self.oidc_scope = oidc_scope
        self.expires_key = EXPIRES_KEY_IN_OIDC

        # TODO(elie): Support using refresh tokens, as opposed to authenticating again
        #   in OIDC.
        self.should_use_refresh_tokens = False

    @classmethod
    def get_valid_keys(cls):
        return super().get_valid_keys() + ["oidc_scope"]

    def _raise_if_missing_params(self):

        self._raise_if_missing_token_params()
        self._raise_if_missing_user_id()
        self._raise_if_missing_backend_params()

        if not self.auth_api_token_url or not self.api_key or not self.secret:
            raise MonaInitializationException(
                "MonaAuth is initiated with missing params. "
                "Please provide auth_api_token_url, api_key and secret."
            )

    def request_access_token(self):
        data_kwargs = {
            "client_id": self.api_key,
            "client_secret": self.secret,
            "grant_type": CLIENT_CREDENTIALS_GRANT_TYPE,
        }

        if self.oidc_scope:
            data_kwargs["scope"] = self.oidc_scope

        return requests.request(
            "POST",
            self.auth_api_token_url,
            headers=URL_ENCODED_HEADER,
            data={**data_kwargs},
        )

    def request_refresh_token(self):
        raise NotImplementedError

    def get_auth_header(self):
        token = get_current_token_by_api_key(
            api_key=self.api_key, access_token_key=OIDC_ACCESS_TOKEN_KEY
        )

        return BaseAuthenticator.create_auth_headers(token)
