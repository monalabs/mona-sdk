from mona_sdk.auth.auth_globals import (
    MONA_AUTH_MODE,
    OIDC_AUTH_MODE,
    MANUAL_TOKEN_AUTH_MODE,
    NO_AUTH_MODE,
)
from mona_sdk.auth.auth_classes.manual_token_auth import ManualTokenAuth
from mona_sdk.auth.auth_classes.mona_auth import MonaAuth
from mona_sdk.auth.auth_classes.no_auth import NoAuth
from mona_sdk.auth.auth_classes.oidc_auth import OidcAuth


AUTH_MODE_TO_AUTHENTICATOR_CLASS = {
    MONA_AUTH_MODE: MonaAuth,
    OIDC_AUTH_MODE: OidcAuth,
    MANUAL_TOKEN_AUTH_MODE: ManualTokenAuth,
    NO_AUTH_MODE: NoAuth,
}


def get_authenticator(auth_mode, should_use_authentication, **kwargs):
    # For backward compatibility.
    if not should_use_authentication:
        return NoAuth(**kwargs)

    return AUTH_MODE_TO_AUTHENTICATOR_CLASS[auth_mode](**kwargs)
