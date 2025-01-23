import os

from client_util import get_boolean_value_for_env_var

OIDC_AUTH_MODE = get_boolean_value_for_env_var("MONA_SDK_OIDC_AUTH_MODE", False)
FRONTEGG_AUTH_MODE = get_boolean_value_for_env_var("MONA_SDK_FRONTEGG_AUTH_MODE", True)

if FRONTEGG_AUTH_MODE and OIDC_AUTH_MODE:
    raise Exception("Both FRONTEGG_AUTH_MODE and OIDC_AUTH_MODE are on")

if not FRONTEGG_AUTH_MODE and not OIDC_AUTH_MODE:
    raise Exception("Both FRONTEGG_AUTH_MODE and OIDC_AUTH_MODE are off")


USE_REFRESH_TOKENS = get_boolean_value_for_env_var("MONA_SDK_USE_REFRESH_TOKENS", True)
