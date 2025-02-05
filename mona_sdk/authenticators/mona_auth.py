import requests

from mona_sdk.auth_globals import EXPIRES_KEY_IN_MONA
from mona_sdk.auth_requests import BASIC_HEADER
from mona_sdk.authenticators.base_auth import Base


class MonaAuth(Base):
    def __init__(self, auth_api_token_url, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._auth_api_token_url = auth_api_token_url
        self.expires_key = EXPIRES_KEY_IN_MONA

    def initial_auth(self):
        pass

    def request_access_token(self):
        return requests.request(
            "POST",
            # todo just make sure that we the correct value here
            self._auth_api_token_url,
            headers=BASIC_HEADER,
            json={"clientId": self.api_key, "secret": self.secret},
        )
