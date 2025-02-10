from mona_sdk.auth.globals import (
    NO_AUTH_MODE,
    MONA_AUTH_MODE,
    OIDC_AUTH_MODE,
    MANUAL_TOKEN_AUTH_MODE,
)
from mona_sdk.auth.authenticators.no_auth import NoAuth
from mona_sdk.auth.authenticators.mona import MonaAuth
from mona_sdk.auth.authenticators.oidc import OidcAuth
from mona_sdk.auth.authenticators.manual_token import ManualTokenAuth

AUTH_MODE_TO_AUTHENTICATOR_CLASS = {
    MONA_AUTH_MODE: MonaAuth,
    OIDC_AUTH_MODE: OidcAuth,
    MANUAL_TOKEN_AUTH_MODE: ManualTokenAuth,
    NO_AUTH_MODE: NoAuth,
}


def get_authenticator(auth_mode, should_use_authentication, **kwargs):
    # For backward compatibility.

    # todo nemo
    if not should_use_authentication:
        return NoAuth(**kwargs)

    return AUTH_MODE_TO_AUTHENTICATOR_CLASS[auth_mode](**kwargs)
