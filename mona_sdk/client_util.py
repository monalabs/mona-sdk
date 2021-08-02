import os


def get_boolean_value_for_env_var(env_var, default_value):
    return {"True": True, "true": True, "False": False, "false": False}.get(
        os.environ.get(env_var), default_value
    )


def is_dict_contains_fields(message_event, required_fields):
    return all((field in message_event for field in required_fields))


def set_env_vars(
    raise_authentication_exceptions,
    raise_export_exception,
    raise_config_exception,
    num_of_retries_for_authentication,
    wait_time_for_authentication_retries,
):
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
