import os


def ged_dict_with_filtered_out_none_values(message):
    return {key: val for key, val in message.items() if val is not None}


def get_boolean_value_for_env_var(env_var, default_value):
    return {"True": True, "true": True, "False": False, "false": False}.get(
        os.environ.get(env_var), default_value
    )
