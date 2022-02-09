import os


def get_boolean_value_for_env_var(env_var, default_value):
    return {"True": True, "true": True, "False": False, "false": False}.get(
        os.environ.get(env_var), default_value
    )


def is_dict_contains_fields(message_event, required_fields):
    return all((field in message_event for field in required_fields))


def remove_items_by_value(data, value_to_remove):
    """
    Return a copy of the given dict after removing the items with value_to_remove as
    value.
    """
    return {key: value for key, value in data.items() if value != value_to_remove}
