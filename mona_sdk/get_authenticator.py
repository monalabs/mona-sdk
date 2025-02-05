from mona_sdk.auth_globals import (
    MONA_AUTH_MODE,
    OIDC_AUTH_MODE,
    MANUAL_TOKEN_AUTH_MODE,
    NO_AUTH_MODE,
)
from mona_sdk.authenticators.manual_token_auth import ManualTokenAuth
from mona_sdk.authenticators.mona_auth import MonaAuth
from mona_sdk.authenticators.no_auth import NoAuth
from mona_sdk.authenticators.oidc_auth import OidcAuth
from mona_sdk.client_exceptions import MonaInitializationException


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


def _raise_if_missing_params(
    auth_mode,
    user_id,
    override_app_server_host,
    override_app_server_full_url,
    override_rest_api_host,
    override_rest_api_full_url,
):
    if auth_mode == MONA_AUTH_MODE:
        return

    if not user_id:
        raise MonaInitializationException(
            f"Mona Client is initiated with an auth mode " f"that requires user_id."
        )

    if (
        not override_rest_api_host
        and not override_rest_api_full_url
        and not override_app_server_host
        and not override_app_server_full_url
    ):
        raise MonaInitializationException(
            "Mona client is initiated with an "
            "auth mode the requires a host or a "
            "full url."
        )


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
    api_key,
    secret,
    access_token,
    user_id,
    should_use_authentication,
    override_rest_api_full_url,
    override_rest_api_host,
    override_app_server_host,
    override_app_server_full_url,
    auth_api_token_url,
    num_of_retries_for_authentication,
    wait_time_for_authentication_retries,
    raise_authentication_exceptions,
):

    # todo think if we want to use au
    auth_mode = _get_auth_mode(
        should_use_authentication,
        access_token,
        override_rest_api_full_url,
        override_rest_api_host,
        override_app_server_host,
        override_app_server_full_url,
    )

    _raise_if_missing_params(
        auth_mode,
        user_id,
        override_app_server_host,
        override_app_server_full_url,
        override_rest_api_host,
        override_rest_api_full_url,
    )

    return AUTH_MODE_TO_AUTHENTICATOR_CLASS[auth_mode](
        api_key,
        secret,
        auth_api_token_url,
        access_token,
        # todo those are three things here that are important.
        num_of_retries_for_authentication,
        wait_time_for_authentication_retries,
        raise_authentication_exceptions,
    )
