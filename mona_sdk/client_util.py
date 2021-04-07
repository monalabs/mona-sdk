import os


def get_boolean_value_for_env_var(env_var, default_value):
    return {"True": True, "true": True, "False": False, "false": False}.get(
        os.environ.get(env_var), default_value
    )


def is_dict_contains_fields(message_event, required_fields):
    return all((field in message_event for field in required_fields))
