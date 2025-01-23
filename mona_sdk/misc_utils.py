def ged_dict_with_filtered_out_none_values(message):
    return {key: val for key, val in message.items() if val is not None}
