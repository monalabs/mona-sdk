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


# todo we might want to move this from here
# @dataclass
# class AuthData:
#     api_key: str
#     secret: str
#     manual_access_token: str
#     oidc_scope: str
#     num_of_retries_for_authentication: int
#     wait_time_for_authentication_retries: int
#     raise_authentication_exceptions: bool

AUTH_MODE_TO_AUTHENTICATOR_CLASS = {
    MONA_AUTH_MODE: MonaAuth,
    OIDC_AUTH_MODE: OidcAuth,
    MANUAL_TOKEN_AUTH_MODE: ManualTokenAuth,
    NO_AUTH_MODE: NoAuth,
}

def _get_auth_mode(
    should_use_authentication,
    access_token,
    override_rest_api_full_url,
    override_rest_api_host,
    override_app_server_host,
    override_app_server_full_url,
):
    # todo allow to force a mode here.

    if not should_use_authentication:
        return NO_AUTH_MODE

    if access_token:
        return MANUAL_TOKEN_AUTH_MODE

    if (
        override_app_server_host
        or override_app_server_full_url
        or override_rest_api_host
        or override_rest_api_full_url
    ):
        return OIDC_AUTH_MODE

    return MONA_AUTH_MODE


def get_authenticator(
    should_use_authentication,
    access_token,
    override_rest_api_full_url,
    override_rest_api_host,
    override_app_server_host,
    override_app_server_full_url,
    **kwargs
):

    auth_mode = _get_auth_mode(
        should_use_authentication,
        access_token,
        override_rest_api_full_url,
        override_rest_api_host,
        override_app_server_host,
        override_app_server_full_url,
    )

    return AUTH_MODE_TO_AUTHENTICATOR_CLASS[auth_mode](
        access_token=access_token,
        override_rest_api_full_url=override_rest_api_full_url,
        override_rest_api_host=override_rest_api_host,
        override_app_server_host=override_app_server_host,
        override_app_server_full_url=override_app_server_full_url,
        **kwargs
    )
