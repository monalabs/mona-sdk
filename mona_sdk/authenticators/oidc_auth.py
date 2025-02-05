from abc import abstractmethod

import requests

from mona_sdk.auth_globals import IS_AUTHENTICATED, EXPIRES_KEY_IN_OIDC, TIME_TO_REFRESH
from mona_sdk.auth_requests import CLIENT_CREDENTIALS_GRANT_TYPE, URLENCODED_HEADER
from mona_sdk.authenticators.base_auth import Base


class OidcAuth(Base):
    # tooo maybe shouldn't support this thing with args at all?
    def __init__(self, api_key, auth_api_token_url, *args, oidc_scope=None, **kwargs):
        super().__init__(api_key, *args, **kwargs)
        self._auth_api_token_url = auth_api_token_url
        self.oidc_scope = oidc_scope
        self.expires_key = EXPIRES_KEY_IN_OIDC


    def _request_access_token_with_retries(self):
        pass

    def initial_auth(self):
        pass

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
            self._auth_api_token_url,
            headers=URLENCODED_HEADER,
            data={**data_kwargs},
        )
