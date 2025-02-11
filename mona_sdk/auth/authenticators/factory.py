from mona_sdk.auth.authenticators.manual_token import ManualTokenAuth
from mona_sdk.auth.authenticators.mona import MonaAuth
from mona_sdk.auth.authenticators.no_auth import NoAuth
from mona_sdk.auth.authenticators.oidc import OidcAuth
from mona_sdk.auth.globals import NO_AUTH_MODE, MONA_AUTH_MODE, OIDC_AUTH_MODE, \
    MANUAL_TOKEN_AUTH_MODE


def get_authenticator(auth_mode, should_use_authentication, **kwargs):

    # For backward compatibility.
    cls = AUTH_MODE_MAP[auth_mode if should_use_authentication else NO_AUTH_MODE]
    valid_keys = cls.get_valid_keys()

    filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_keys}
    return cls(**filtered_kwargs)


AUTH_MODE_MAP = {
    MONA_AUTH_MODE: MonaAuth,
    OIDC_AUTH_MODE: OidcAuth,
    MANUAL_TOKEN_AUTH_MODE: ManualTokenAuth,
    NO_AUTH_MODE: NoAuth,
}
