import os
import json
import random
import hashlib
from json import JSONDecodeError

from mona_sdk.client_exceptions import MonaInitializationException

NORMALIZED_HASH_DECIMAL_DIGITS = 7
NORMALIZED_HASH_PRECISION = 10**NORMALIZED_HASH_DECIMAL_DIGITS


def get_boolean_value_for_env_var(env_var, default_value):
    return {"True": True, "true": True, "False": False, "false": False}.get(
        os.environ.get(env_var), default_value
    )


def get_dict_value_for_env_var(env_var, cast_values=None, default_value=None):
    """
    Expects a valid json string (or empty). cast_values allows to cast (and verify
    success of casting) all values to the given type.
    """
    value = os.environ.get(env_var)
    if not value:
        return default_value
    try:
        config = json.loads(value)
        if type(config) is not dict:
            raise MonaInitializationException(
                f'Env {env_var} isn\'t a valid json *Object*. Received: "{value}"'
            )
        if cast_values:
            for key in config:
                config[key] = cast_values(config[key])
        return config
    except JSONDecodeError:
        raise MonaInitializationException(
            f'Env {env_var} must be a valid json string. Received: "{value}"'
        )
    except ValueError:
        raise MonaInitializationException(
            f"Env {env_var} object values must be of type {cast_values}."
        )


def is_dict_contains_fields(message_event, required_fields):
    return all((field in message_event for field in required_fields))


def remove_items_by_value(data, value_to_remove):
    """
    Return a copy of the given dict after removing the items with value_to_remove as
    value.
    """
    return {key: value for key, value in data.items() if value != value_to_remove}


def _calculate_normalized_hash(context_id):
    """
    Calculate a normalized hash of a context id (a fraction between 0 to 1).
    """
    context_id_encoded = context_id.encode("ascii")
    # We chose sha224 here to have a different and independent hashing than sha1 which
    # is used on our end for similar purposes.
    return (
        int(hashlib.sha224(context_id_encoded).hexdigest(), base=16)
        % NORMALIZED_HASH_PRECISION
    ) / NORMALIZED_HASH_PRECISION


def keep_message_after_sampling(context_id, sampling_rate):
    if context_id:
        return _calculate_normalized_hash(context_id) <= sampling_rate
    else:
        # TODO(Nemo): Allow getting seed from the user for random.random().
        return random.random() <= sampling_rate


def get_dict_result(success, data, error_message):
    return {"success": success, "data": data, "error_message": error_message}
