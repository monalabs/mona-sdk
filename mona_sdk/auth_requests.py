import os

import requests
from mona_sdk.auth_master_swithces import OIDC_AUTH_MODE, FRONTEGG_AUTH_MODE

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


def _request_access_token_once(api_key, secret, oidc_scope=None):
    """
    Sends an access token REST request and returns the response.
    """

    if FRONTEGG_AUTH_MODE:
        return requests.request(
            "POST",
            AUTH_API_TOKEN_URL,
            headers=BASIC_HEADER,
            json={"clientId": api_key, "secret": secret},
        )

    if OIDC_AUTH_MODE:
        data_kwargs = {
            "client_id": api_key,
            "client_secret": secret,
            "grant_type": CLIENT_CREDENTIALS_GRANT_TYPE,
        }

        if oidc_scope:
            data_kwargs["scope"] = oidc_scope

        return requests.request(
            "POST",
            AUTH_API_TOKEN_URL,
            headers=URLENCODED_HEADER,
            data={**data_kwargs},
        )


def _request_refresh_token_once(refresh_token_key):
    """
    Sends a refresh token REST request and returns the response.
    """
    return requests.request(
        "POST",
        REFRESH_TOKEN_URL,
        headers=BASIC_HEADER,
        json={"refreshToken": refresh_token_key},
    )
