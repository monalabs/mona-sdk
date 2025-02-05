import os

import requests
from mona_sdk.auth_globals import AUTH_MODE, OIDC_AUTH_MODE, MONA_AUTH_MODE

AUTH_API_TOKEN_URL = os.environ.get(
    "MONA_SDK_AUTH_API_TOKEN_URL",
    "https://monalabs.frontegg.com/identity/resources/auth/v1/api-token",
)
REFRESH_TOKEN_URL = os.environ.get(
    "MONA_SDK_REFRESH_TOKEN_URL",
    "https://monalabs.frontegg.com/identity/resources/auth/v1/api-token/"
    "token/refresh",
)
CLIENT_CREDENTIALS_GRANT_TYPE = "client_credentials"
BASIC_HEADER = {"Content-Type": "application/json"}
URLENCODED_HEADER = {"Content-Type": "application/x-www-form-urlencoded"}


# todo I think that different classes should have different functions then









def request_refresh_token_once(refresh_token_key):
    """
    Sends a refresh token REST request and returns the response.
    """
    return requests.request(
        "POST",
        REFRESH_TOKEN_URL,
        headers=BASIC_HEADER,
        json={"refreshToken": refresh_token_key},
    )
