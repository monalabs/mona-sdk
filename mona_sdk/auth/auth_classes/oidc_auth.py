import datetime
from abc import abstractmethod

import requests

from mona_sdk.auth.auth_globals import EXPIRES_KEY_IN_OIDC, TIME_TO_REFRESH_INTERNAL_KEY
from mona_sdk.auth.auth_requests import CLIENT_CREDENTIALS_GRANT_TYPE, URLENCODED_HEADER
from mona_sdk.auth.auth_classes.base_auth import Base
from mona_sdk.auth.auth_utils import get_token_info_by_api_key
from mona_sdk.client_exceptions import MonaInitializationException


class OidcAuth(Base):
    # todo maybe shouldn't support this thing with args at all?
    def __init__(self, api_key, *args, oidc_scope=None, **kwargs):
        super().__init__(api_key, *args, **kwargs)
        self.oidc_scope = oidc_scope
        self.expires_key = EXPIRES_KEY_IN_OIDC

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

    # todo interesting how to implement this
    @abstractmethod
    def refresh_token(self):
        pass

    def request_access_token(self):
        data_kwargs = {
            "client_id": self.api_key,
            "client_secret": self.secret,
            "grant_type": CLIENT_CREDENTIALS_GRANT_TYPE,
        }

        # todo make sure we pass this somewhere
        if self.oidc_scope:
            data_kwargs["scope"] = self.oidc_scope

        return requests.request(
            "POST",
            # todo think where is this going to come from
            self.auth_api_token_url,
            headers=URLENCODED_HEADER,
            data={**data_kwargs},
        )

    # todo this is not the right place here.
    # TODO(elie): Support refresh tokens in OIDC.
