"""
This module contains all user-configurable environment variables.
"""
import os

from mona_sdk.client_util import get_boolean_value_for_env_var


# Note: if RAISE_AUTHENTICATION_EXCEPTIONS = False and the client could not
# authenticate, every function call will return false.
# Use client.is_active() in order to check authentication status.
def _get_raise_authentication_exception_env_var():
    return get_boolean_value_for_env_var(
        "MONA_SDK_RAISE_AUTHENTICATION_EXCEPTIONS", False
    )


def _get_raise_export_exception_env_var():
    return get_boolean_value_for_env_var("MONA_SDK_RAISE_EXPORT_EXCEPTIONS", False)


def _get_raise_config_exception_env_var():
    return get_boolean_value_for_env_var("MONA_SDK_RAISE_CONFIG_EXCEPTIONS", False)


def _get_num_of_retries_for_authentication_env_var():
    """
    Return the number of retries to authenticate in case the authentication server
    failed to respond.
    """
    return int(os.environ.get("MONA_SDK_NUM_OF_RETRIES_FOR_AUTHENTICATION", 3))


def _get_wait_time_for_authentication_retries_sec_env_var():
    """
    Return the time to wait (in seconds) between retries in case the authentication
    server failed to respond.
    """
    return int(os.environ.get("MONA_SDK_WAIT_TIME_FOR_AUTHENTICATION_RETRIES_SEC", 2))


ENV_VARS_GETTERS_MAP = {
    "MONA_SDK_RAISE_AUTHENTICATION_EXCEPTIONS": (
        _get_raise_authentication_exception_env_var
    ),
    "MONA_SDK_RAISE_EXPORT_EXCEPTIONS": _get_raise_export_exception_env_var,
    "MONA_SDK_RAISE_CONFIG_EXCEPTIONS": _get_raise_config_exception_env_var,
    "MONA_SDK_NUM_OF_RETRIES_FOR_AUTHENTICATION": (
        _get_num_of_retries_for_authentication_env_var
    ),
    "MONA_SDK_WAIT_TIME_FOR_AUTHENTICATION_RETRIES_SEC": (
        _get_wait_time_for_authentication_retries_sec_env_var
    ),
}


def get_env_var(env_var_name):
    return ENV_VARS_GETTERS_MAP[env_var_name]()


def set_env_vars(
    raise_authentication_exceptions,
    raise_export_exception,
    raise_config_exception,
    num_of_retries_for_authentication,
    wait_time_for_authentication_retries,
):
    """
    Change the values of the given env vars.
    """
    env_vars = {
        "MONA_SDK_RAISE_AUTHENTICATION_EXCEPTIONS": raise_authentication_exceptions,
        "MONA_SDK_RAISE_EXPORT_EXCEPTIONS": raise_export_exception,
        "MONA_SDK_RAISE_CONFIG_EXCEPTIONS": raise_config_exception,
        "MONA_SDK_NUM_OF_RETRIES_FOR_AUTHENTICATION": num_of_retries_for_authentication,
        "MONA_SDK_WAIT_TIME_FOR_AUTHENTICATION_RETRIES_SEC": (
            wait_time_for_authentication_retries
        ),
    }

    for env_var in env_vars:
        if env_vars[env_var] is not None:
            os.environ[env_var] = env_vars[env_var]

