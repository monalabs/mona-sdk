# ----------------------------------------------------------------------------
#    Copyright 2021 MonaLabs.io
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
# ----------------------------------------------------------------------------
"""
This module contains all validation functions for client use.
"""
import json
import collections.abc

from .logger import get_logger
from .client_util import is_dict_contains_fields
from .client_exceptions import MonaExportException


def mona_messages_to_dicts_validation(
    events, raise_export_exceptions, log_failed_messages
):
    try:
        # Get all MonsSingleMessage as dicts.
        dict_events = [message.get_dict() for message in events]
    except TypeError:
        return handle_export_error(
            "export_batch must get an iterable of MonaSingleMessage.",
            raise_export_exceptions,
            events if log_failed_messages else None,
        )
    except AttributeError:
        return handle_export_error(
            "Messages exported to Mona must be MonaSingleMessage.",
            raise_export_exceptions,
            events if log_failed_messages else None,
        )

    # Validate that the batch is json serializable.
    if not _is_json_serializable(dict_events):
        return handle_export_error(
            "All fields in MonaSingleMessage must be JSON serializable.",
            raise_export_exceptions,
            events if log_failed_messages else None,
        )

    return dict_events


def _is_json_serializable(message):
    """
    Validates if the given message is a jsonable string.
    """
    try:
        json.dumps(message)
    except TypeError:
        return False

    return True


def validate_mona_single_message(message_event):
    # Check that message_event contains all required fields.
    required_fields = ("message", "contextClass")

    return is_dict_contains_fields(message_event, required_fields)


def update_mona_fields_names(message):
    """
    Changes names of fields that starts with "MONA_" to start with "MY_MONA_"
    """
    message_copy = dict(message)
    for key in message:
        if key.startswith("MONA_"):
            message_copy[f"MY_{key}"] = message_copy.pop(key)

    return message_copy


def validate_inner_message_type(message):
    """
    Validates the given input is a valid message (should be JSON serializable).
    """
    if not isinstance(message, collections.abc.Mapping):
        get_logger().error("Tried to send non-dict message to mona")
        return False

    return True


def handle_export_error(error_message, should_raise_exception, failed_message):
    """
    Logs an error and raises MonaExportException if RAISE_EXPORT_EXCEPTIONS is true,
    else returns false.
    """
    get_logger().error(error_message)
    if failed_message:
        get_logger().error(
            f"Failed to send the following to mona: {failed_message}"
        )
    if should_raise_exception:
        raise MonaExportException(error_message)
    return False
