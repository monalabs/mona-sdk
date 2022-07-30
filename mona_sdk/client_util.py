import os
import hashlib

NORMALIZED_HASH_DECIMAL_DIGITS = 7
NORMALIZED_HASH_PRECISION = 10 ** NORMALIZED_HASH_DECIMAL_DIGITS


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


def calculate_normalized_hash(context_id):
    """
    Calculate a normalized hash of a string id (a fraction between 0 to 1).
    """
    context_id_encoded = context_id.encode("ascii")
    return (
        int(hashlib.sha224(context_id_encoded).hexdigest(), base=16)
        % NORMALIZED_HASH_PRECISION
    ) / NORMALIZED_HASH_PRECISION
