import os
import datetime
from os import environ

from mona_sdk.client_util import get_boolean_value_for_env_var

EXPIRES_KEY_IN_MONA = "expiresIn"
EXPIRES_KEY_IN_OIDC = "expires_in"

OIDC_ACCESS_TOKEN_KEY = "access_token"
MONA_ACCESS_TOKEN_KEY = "accessToken"
MANUAL_ACCESS_TOKEN_KEY = "accessToken"

MONA_REFRESH_TOKEN_KEY = "refreshToken"

ERRORS_INTERNAL_KEY = "errors"
TIME_TO_REFRESH_INTERNAL_KEY = "timeToRefresh"
IS_AUTHENTICATED_INTERNAL_KEY = "isAuthenticated"
MANUAL_TOKEN_STRING_FOR_API_INTERNAL_KEY = "manual_token_mode"

CLIENT_CREDENTIALS_GRANT_TYPE = "client_credentials"
BASIC_HEADER = {"Content-Type": "application/json"}
URL_ENCODED_HEADER = {"Content-Type": "application/x-www-form-urlencoded"}

OIDC_AUTH_MODE = "OIDC"
MONA_AUTH_MODE = "MONA"
MANUAL_TOKEN_AUTH_MODE = "MANUAL_TOKEN"
NO_AUTH_MODE = "NO_AUTH"


# This is currently relevant only to the "Mona" auth mode.
SHOULD_USE_REFRESH_TOKENS = get_boolean_value_for_env_var(
    "MONA_SDK_USE_REFRESH_TOKENS", True
)

SHOULD_USE_AUTHENTICATION = get_boolean_value_for_env_var(
    "MONA_SDK_SHOULD_USE_AUTHENTICATION", True
)

AUTH_MODE = environ.get(
    "AUTH_MODE",
    MONA_AUTH_MODE,
)

AUTH_API_TOKEN_URL = os.environ.get(
    "MONA_SDK_AUTH_API_TOKEN_URL",
    "https://monalabs.frontegg.com/identity/resources/auth/v1/api-token",
)
REFRESH_TOKEN_URL = os.environ.get(
    "MONA_SDK_REFRESH_TOKEN_URL",
    "https://monalabs.frontegg.com/identity/resources/auth/v1/api-token/"
    "token/refresh",
)


# As of 29/1/2025, a new token expires after 4 hours. REFRESH_TOKEN_SAFETY_MARGIN is the
# safety gap of time to refresh the token before it expires (i.e. - in case
# REFRESH_TOKEN_SAFETY_MARGIN = 2, and the token is about to expire in 2 hours or less,
# the client will automatically refresh the token to a new one).
REFRESH_TOKEN_SAFETY_MARGIN = datetime.timedelta(
    hours=int(
        os.environ.get("MONA_SDK_REFRESH_TOKEN_SAFETY_MARGIN", 0.5),
    )
)

OIDC_CLIENT_ID = os.environ.get("MONA_SDK_OIDC_CLIENT_ID")
OIDC_CLIENT_SECRET = os.environ.get("MONA_SDK_OIDC_CLIENT_SECRET")
OIDC_SCOPE = os.environ.get("MONA_SDK_OIDC_SCOPE")

ACCESS_TOKEN = os.environ.get("MONA_SDK_ACCESS_TOKEN")

API_KEY = os.environ.get("MONA_SDK_API_KEY")
SECRET = os.environ.get("MONA_SDK_SECRET")
USER_ID = os.environ.get("MONA_SDK_USER_ID")
