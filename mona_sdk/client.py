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
import os
from json import JSONDecodeError
from typing import List
from dataclasses import dataclass

import jwt
import requests
from requests.exceptions import ConnectionError

from mona_sdk.client_exceptions import MonaConfigUploadException
from .client_util import get_boolean_value_for_env_var
from .logger import get_logger
from .validation import (
    handle_export_error,
    update_mona_fields_names,
    validate_inner_message_type,
    validate_mona_single_message,
    mona_messages_to_dicts_validation,
)
from .authentication import (
    Decorators,
    is_authenticated,
    first_authentication,
    get_current_token_by_api_key,
    get_basic_auth_header,
)

# Note: if RAISE_AUTHENTICATION_EXCEPTIONS = False and the client could not
# authenticate, every function call will return false.
# Use client.is_active() in order to check authentication status.
RAISE_AUTHENTICATION_EXCEPTIONS = get_boolean_value_for_env_var(
    "MONA_SDK_RAISE_AUTHENTICATION_EXCEPTIONS", False
)

RAISE_EXPORT_EXCEPTIONS = get_boolean_value_for_env_var(
    "MONA_SDK_RAISE_EXPORT_EXCEPTIONS", False
)

RAISE_CONFIG_EXCEPTIONS = get_boolean_value_for_env_var(
    "MONA_SDK_RAISE_CONFIG_EXCEPTIONS", False
)

# Number of retries to authenticate in case the authentication server failed to
# respond.
NUM_OF_RETRIES_FOR_AUTHENTICATION = int(
    os.environ.get("MONA_SDK_NUM_OF_RETRIES_FOR_AUTHENTICATION", 3)
)

# Time to wait (in seconds) between retries in case the authentication server failed to
# respond.
WAIT_TIME_FOR_AUTHENTICATION_RETRIES_SEC = int(
    os.environ.get("MONA_SDK_WAIT_TIME_FOR_AUTHENTICATION_RETRIES_SEC", 2)
)

# When this variable is True, failed messages (for any reason) will be logged at "Error"
# level.
SHOULD_LOG_FAILED_MESSAGES = get_boolean_value_for_env_var(
    "MONA_SDK_SHOULD_LOG_FAILED_MESSAGES", False
)

GET_CONFIG_ERROR_MESSAGE = "Could not get server response with the current config."
UPLOAD_CONFIG_ERROR_MESSAGE = (
    "Could not upload the new configuration, please check it is valid."
)
APP_SERVER_CONNECTION_ERROR_MESSAGE = "Cannot connect to app-server."


@dataclass
class MonaSingleMessage:
    """
    Class for keeping properties for a single Mona Message.
    Attributes:
        :param message (dict): (Required) JSON serializable dict with properties to send
            about the context ID.
        :param contextClass (str): (Required) context classes are defined in the Mona
            Config and define the schema of the contexts.
        :param contextId (str): (Optional) A unique identifier for the current context
            instance. One can export multiple messages with the same context_id and Mona
            would aggregate all of these messages to one big message on its backend.
            If none is given, Mona will create a random uuid for it. This is highly
            unrecommended - since it takes away the option to update this data in the
            future.
        :param exportTimestamp (int|str): (Optional) This is the primary timestamp Mona
            will use when considering the data being sent. It should be a date (ISO
            string or a Unix time number) representing the time the message was created.
            If not supplied, current time is used.


    A new message initialization would look like this:
    message_to_mona = MonaSingleMessage(
        message=<the relevant monitoring information>,
        contextClass="MY_CONTEXT_CLASS_NAME",
        contextId=<the context instance unique id>,
        exportTimestamp=<the message export timestamp>,
    )
    """

    message: dict
    contextClass: str
    contextId: str = None
    exportTimestamp: int or str = None

    def get_dict(self):
        return {
            key: value
            for key, value in self.__dict__.items()
            if key in MonaSingleMessage.__dataclass_fields__.keys()
        }


class Client:
    """
    The main Mona python client class. Use this class to communicate with any of Mona's
    API.
    """

    def __init__(
        self,
        api_key,
        secret,
        raise_authentication_exceptions=RAISE_AUTHENTICATION_EXCEPTIONS,
        raise_export_exceptions=RAISE_EXPORT_EXCEPTIONS,
        raise_config_exceptions=RAISE_CONFIG_EXCEPTIONS,
        num_of_retries_for_authentication=NUM_OF_RETRIES_FOR_AUTHENTICATION,
        wait_time_for_authentication_retries=WAIT_TIME_FOR_AUTHENTICATION_RETRIES_SEC,
        should_log_failed_messages=SHOULD_LOG_FAILED_MESSAGES,
    ):
        """
        Creates the Client object. this client is lightweight so it can be regenerated
        or reused to user convenience.
        :param api_key: An api key provided to you by Mona.
        :param secret: The secret corresponding to the given api_key.
        """
        self._logger = get_logger()
        self.api_key = api_key
        self.secret = secret

        self.raise_authentication_exceptions = raise_authentication_exceptions
        self.raise_export_exceptions = raise_export_exceptions
        self.raise_config_exceptions = raise_config_exceptions
        self.num_of_retries_for_authentication = num_of_retries_for_authentication
        self.wait_time_for_authentication_retries = wait_time_for_authentication_retries
        self.should_log_failed_messages = should_log_failed_messages

        could_authenticate = first_authentication(self)
        if not could_authenticate:
            return

        # Update user's mona url for future requests.
        self._user_id = self._get_user_id()
        self._rest_api_url = f"https://incoming{self._user_id}.monalabs.io/export"
        self._app_server_url = f"https://api{self._user_id}.monalabs.io"

    def is_active(self):
        """
        Returns True if the client is authenticated (or able to re-authenticate when
        needed) and therefore can export messages, otherwise returns False, meaning the
        client cannot export data to Mona's servers.
        Use this method to check client status in case RAISE_AUTHENTICATION_EXCEPTIONS
        is set to False.
        """
        return is_authenticated(self.api_key)

    def _get_user_id(self):
        """
        :return: The customer's user id (tenant id).
        """
        decoded_token = jwt.decode(
            get_current_token_by_api_key(self.api_key), verify=False
        )
        return decoded_token["tenantId"]

    @Decorators.refresh_token_if_needed
    def export(self, message: MonaSingleMessage):
        """
        Exports a single message to Mona's systems.

        :param message: MonaSingleMessage (required)
            message should be a MonaSingleMessage instance, which is a dataclass
            provided in this module.
        :return: boolean
            True if the message was successfully sent to Mona's systems,
            False otherwise (failure reason will be logged).
        """
        export_result = self._export_batch_inner([message])
        return export_result and export_result["failed"] == 0

    @Decorators.refresh_token_if_needed
    def export_batch(self, events: List[MonaSingleMessage]):
        """
        Use this function to easily send a batch of MonaSingleMessage to Mona.
        :param events: List[MonaSingleMessage]
            Events should be a list of MonaSingleMessage (provided in this module).
        :return: dict
            Returns a dict of the following format:
            {
                "total": <number of messages event in batch>,
                "sent": <number of messages event successfully sent>,
                "failed": <number of messages event failed to be sent>
                "failure_reason": a dict of failed messages (index and contextId) and
                                  for each message the reason it failed.
            }
        """
        return self._export_batch_inner(events)

    def _export_batch_inner(self, events: List[MonaSingleMessage]):
        events = mona_messages_to_dicts_validation(
            events, self.raise_export_exceptions, self.should_log_failed_messages
        )
        if not events:
            return False

        messages_to_send = []
        for message_event in events:
            if not validate_mona_single_message(message_event):
                return handle_export_error(
                    "Messages to export must be of MonaSingleMessage type.",
                    self.raise_export_exceptions,
                    events if self.should_log_failed_messages else None,
                )

            message_copy = dict(message_event)

            # TODO(anat): remove the following line once REST-api allows "contextClass"
            #  instead of "arcClass".
            message_copy["arcClass"] = message_copy.pop("contextClass")

            # TODO(anat): Add full validations on client side.
            if validate_inner_message_type(message_copy["message"]):
                # Change fields in message that starts with "MONA_".
                message_copy["message"] = update_mona_fields_names(
                    message_copy["message"]
                )

            messages_to_send.append(message_copy)

        # Create and send the rest call to Mona's rest-api.
        try:
            rest_api_response = self._send_mona_rest_api_request(messages_to_send)
        except ConnectionError:
            return handle_export_error(
                "Cannot connect to rest-api",
                self.raise_export_exceptions,
                events if self.should_log_failed_messages else None,
            )

        # Create the response and return it.
        client_response = Client._create_client_response(
            rest_api_response,
            total=len(events),
        )
        if client_response["failed"] > 0:
            handle_export_error(
                f"Some messages didn't pass validation: {client_response}",
                self.raise_export_exceptions,
                events if self.should_log_failed_messages else None,
            )
        else:
            self._logger.info(
                f"All {client_response['total']} messages have been sent."
            )

        return client_response

    def _send_mona_rest_api_request(self, messages):
        """
        Sends a REST call to Mona's servers with the provided messages.
        :return: A REST response.
        """
        return requests.request(
            "POST",
            self._rest_api_url,
            headers=get_basic_auth_header(self.api_key),
            json={"userId": self._user_id, "messages": messages},
        )

    @staticmethod
    def _create_client_response(
        response,
        total,
    ):
        """
        Creates the dict response of the client to an export_batch() call.
        :param response: The response received from the rest-api.
        :param total: total messages in batch.
        :return: A dict with response details (see export_batch docs for format).
        """
        # Sum the number of messaged that Mona's client didn't send to rest-api.
        failed = 0
        failure_reasons = {}

        # Check if some messages didn't passed validation on the rest-api.
        if not response.ok:
            try:
                result_info = response.json()
                failed = result_info["failed"]
                failure_reasons = result_info["failure_reasons"]
            except Exception:
                failed = total
                failure_reasons = "Failed to send the batch to Mona's servers"

        # Return the total result of the batch.
        return {
            "total": total,
            "failed": failed,
            "sent": total - failed,
            "failure_reasons": failure_reasons,
        }

    @Decorators.refresh_token_if_needed
    def upload_config(self, config, commit_message):
        """
        Uploads a new configuration, as a json-serializable dict.
        The configuration file enables you to define how the exported data should be
        aggregated and analyzed in Mona, as well as your insight and alerting
        preferences.
        Find more information on creating your configuration at:
        https://docs.monalabs.io/.
        :param config: (dict) your configuration, no need for your tenant id as key,
        first layer of keys should be the context classes.
        :param commit_message: (str)
        :return: A dict holding the upload data:
        {
            "success": <was the upload successful>, (bool)
            "new_config_id": <the new configuration ID> (str)
        }
        """
        config_to_upload = {
            "config": {self._user_id: config},
            "author": self.api_key,
            "commit_message": commit_message,
            "user_id": self._user_id,
        }
        upload_output = {"success": False, "new_config_id": ""}
        try:
            upload_response = requests.post(
                f"{self._app_server_url}/upload_config",
                headers=get_basic_auth_header(self.api_key),
                json=config_to_upload,
            )
            response_data = upload_response.json()["response_data"]
            upload_output["new_config_id"] = response_data["new_config_id"]
            upload_output["success"] = upload_response.ok

            if not upload_output["success"]:
                # Raise an exception is asked to.
                self._handle_config_error(UPLOAD_CONFIG_ERROR_MESSAGE)

        except ConnectionError:
            # Raise an exception if asked to.
            self._handle_config_error(APP_SERVER_CONNECTION_ERROR_MESSAGE)
        except JSONDecodeError:
            # Raise an exception if asked to.
            self._handle_config_error(UPLOAD_CONFIG_ERROR_MESSAGE)

        return upload_output

    @Decorators.refresh_token_if_needed
    def get_config(self):
        """
        :return: A json-serializable dict with the current defined configuration.
        """
        try:
            config_response = requests.post(
                f"{self._app_server_url}/configs",
                headers=get_basic_auth_header(self.api_key),
                data="{}",
            )
            config_data = config_response.json()
            if not config_response.ok:
                return self._handle_config_error(GET_CONFIG_ERROR_MESSAGE)

        except ConnectionError:
            return self._handle_config_error(APP_SERVER_CONNECTION_ERROR_MESSAGE)
        except JSONDecodeError:
            return self._handle_config_error(GET_CONFIG_ERROR_MESSAGE)

        return {self._user_id: config_data["response_data"]["raw_configuration_data"]}

    def _handle_config_error(self, error_message):
        """
        Logs an error and raises MonaExportException if RAISE_EXPORT_EXCEPTIONS is true,
        else returns false.
        """
        self._logger.error(error_message)
        if self.raise_config_exceptions:
            raise MonaConfigUploadException(error_message)
        return False
