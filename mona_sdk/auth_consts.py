from mona_sdk.auth_master_swithces import OIDC_AUTH_MODE

ERRORS = "errors"

EXPIRES_IN_FRONTEGG = "expiresIn"
EXPIRED_IN_OIDC = "expires_in"

ACCESS_TOKEN_IN_OIDC = "access_token"
ACCESS_TOKEN_IN_FRONTEGG = "accessToken"

REFRESH_TOKEN = "refreshToken"
TIME_TO_REFRESH = "timeToRefresh"

IS_AUTHENTICATED = "isAuthenticated"

MANUAL_TOKEN_STRING_FOR_API_KEY = "manual_token_mode"

ACCESS_TOKEN = ACCESS_TOKEN_IN_OIDC if OIDC_AUTH_MODE else ACCESS_TOKEN_IN_FRONTEGG
