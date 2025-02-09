import datetime
from abc import abstractmethod

import requests

from mona_sdk.auth.auth_globals import EXPIRES_KEY_IN_OIDC, \
    TIME_TO_REFRESH_INTERNAL_KEY, OIDC_ACCESS_TOKEN_KEY
from mona_sdk.auth.auth_requests import CLIENT_CREDENTIALS_GRANT_TYPE, \
    URLENCODED_HEADER, BASIC_HEADER
from mona_sdk.auth.auth_classes.base_auth import Base
from mona_sdk.auth.auth_utils import get_token_info_by_api_key, \
    get_current_token_by_api_key
from mona_sdk.client_exceptions import MonaInitializationException


class OidcAuth(Base):
    def __init__(self, *args, api_key, oidc_scope=None, **kwargs):
        super().__init__(*args, api_key, **kwargs)
        self.oidc_scope = oidc_scope
        self.expires_key = EXPIRES_KEY_IN_OIDC

        # TODO(elie): Support using refresh tokens, as opposed to authenticating again
        #   in OIDC.
        self.should_use_refresh_tokens = False

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
            headers=URLENCODED_HEADER,
            data={**data_kwargs},
        )

    def get_auth_header(self):
        token = get_current_token_by_api_key(
            api_key=self.api_key, access_token_key=OIDC_ACCESS_TOKEN_KEY
        )

        return {
            **BASIC_HEADER,
            "Authorization": f"Bearer {token}",
        }

