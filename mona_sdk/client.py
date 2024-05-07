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
import json
import logging
from json import JSONDecodeError
from typing import List
from dataclasses import dataclass

import jwt
import requests
from cachetools import TTLCache, cached
from requests.exceptions import ConnectionError
from mona_sdk.client_exceptions import MonaServiceException, MonaInitializationException

from .logger import get_logger
from .validation import (
    handle_export_error,
    update_mona_fields_names,
    validate_inner_message_type,
    validate_mona_single_message,
    mona_messages_to_dicts_validation,
)
from .client_util import (
    get_dict_result,
    remove_items_by_value,
    get_dict_value_for_env_var,
    keep_message_after_sampling,
    get_boolean_value_for_env_var,
)
from .authentication import (
    Decorators,
    is_authenticated,
    first_authentication,
    get_basic_auth_header,
    get_current_token_by_api_key,
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

RAISE_SERVICE_EXCEPTIONS = get_boolean_value_for_env_var(
    "MONA_SDK_RAISE_SERVICE_EXCEPTIONS", False
)

SHOULD_USE_AUTHENTICATION = get_boolean_value_for_env_var(
    "MONA_SDK_SHOULD_USE_AUTHENTICATION", True
)

SHOULD_USE_SSL = get_boolean_value_for_env_var("MONA_SDK_SHOULD_USE_SSL", True)

OVERRIDE_APP_SERVER_HOST = os.environ.get("MONA_SDK_OVERRIDE_APP_SERVER_HOST")

# TODO(anat): Once no one is using it, remove this env var (leave only
#  OVERRIDE_REST_API_HOST).
OVERRIDE_REST_API_URL = os.environ.get("MONA_SDK_OVERRIDE_REST_API_URL")
OVERRIDE_REST_API_HOST = os.environ.get("MONA_SDK_OVERRIDE_REST_API_HOST")

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

FILTER_NONE_FIELDS_ON_EXPORT = get_boolean_value_for_env_var(
    "MONA_SDK_FILTER_NONE_FIELDS_ON_EXPORT", False
)

# SDK will randomly sample the sent data using this factor and disregard the sampled-
# out data, unless the sent data is set on a class overridden by
# MONA_SDK_SAMPLING_CONFIG.
DEFAULT_SAMPLING_FACTOR = float(
    os.environ.get("MONA_SDK_DEFAULT_SAMPLING_FACTOR", 1)
)

# When set, SDK will randomly sample the sent data for any class keyed in the config.
# See readme for more details.
SAMPLING_CONFIG = get_dict_value_for_env_var(
    "MONA_SDK_SAMPLING_CONFIG", cast_values=float
)

SAMPLING_CONFIG_NAME = os.environ.get("SAMPLING_CONFIG_NAME")

SAMPLING_FACTORS_MAX_AGE_SECONDS = os.environ.get(
    "SAMPLING_FACTORS_MAX_AGE_SECONDS", 300
)

UNAUTHENTICATED_CHECK_ERROR_MESSAGE = (
    "Notice that should_use_authentication is set to False, which is not supported by "
    "default and must be explicitly requested from Mona team. "
)
SERVICE_ERROR_MESSAGE = "Could not get server response for the wanted service"

RETRIEVE_CONFIG_HISTORY_ERROR_MESSAGE = "Retrieve history is empty"
GET_AGGREGATED_STATS_OF_SPECIFIC_SEGMENTATION_ERROR_MESSAGE = (
    "Could not get aggregates state of a specific segmentation"
)

APP_SERVER_CONNECTION_ERROR_MESSAGE = "Cannot connect to app-server"

CONFIG_MUST_BE_A_DICT_ERROR_MESSAGE = "config must be a dict"

# The argument to use as a default value on the values of the data argument (dict) when
# calling _app_server_request(). Use this and not None in order to be able to pass a
# None argument if needed.
UNPROVIDED_VALUE = "mona_unprovided_value"

# TODO(anat): change the following line once REST-api allows "contextClass"
#  instead of "arcClass".
CONTEXT_CLASS_FIELD_NAME = "arcClass"
CONTEXT_ID_FIELD_NAME = "contextId"

CLIENT_ERROR_RESPONSE_STATUS_CODE = 400
SERVER_ERROR_RESPONSE_STATUS_CODE = 500


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
        :param action (str): (Optional) The action to use on the values in the fields of
            this message - "OVERWRITE", "ADD" or "NEW" (default: "OVERWRITE").


    A new message initialization would look like this:
    message_to_mona = MonaSingleMessage(
        message=<the relevant monitoring information>,
        contextClass="MY_CONTEXT_CLASS_NAME",
        contextId=<the context instance unique id>,
        exportTimestamp=<the message export timestamp>,
        action=<the wanted action>,
    )
    """

    message: dict
    contextClass: str
    contextId: str = None
    exportTimestamp: int or str = None
    action: str = None
    sampleConfigName: str = None

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
        api_key=None,
        secret=None,
        raise_authentication_exceptions=RAISE_AUTHENTICATION_EXCEPTIONS,
        raise_export_exceptions=RAISE_EXPORT_EXCEPTIONS,
        raise_service_exceptions=RAISE_SERVICE_EXCEPTIONS,
        num_of_retries_for_authentication=NUM_OF_RETRIES_FOR_AUTHENTICATION,
        wait_time_for_authentication_retries=WAIT_TIME_FOR_AUTHENTICATION_RETRIES_SEC,
        should_log_failed_messages=SHOULD_LOG_FAILED_MESSAGES,
        should_use_ssl=SHOULD_USE_SSL,
        should_use_authentication=SHOULD_USE_AUTHENTICATION,
        override_rest_api_full_url=OVERRIDE_REST_API_URL,
        override_rest_api_host=OVERRIDE_REST_API_HOST,
        override_app_server_host=OVERRIDE_APP_SERVER_HOST,
        user_id=None,
        filter_none_fields_on_export=FILTER_NONE_FIELDS_ON_EXPORT,
        default_sampling_rate=DEFAULT_SAMPLING_FACTOR,
        context_class_to_sampling_rate=SAMPLING_CONFIG,
        sampling_config_name=SAMPLING_CONFIG_NAME,
    ):
        """
        Creates the Client object. this client is lightweight so it can be regenerated
        or reused to user convenience.
        :param api_key: An api key provided to you by Mona.
        :param secret: The secret corresponding to the given api_key.
        """
        if not should_use_authentication and not user_id:
            raise MonaInitializationException(
                "When MONA_SDK_SHOULD_USE_AUTHENTICATION is turned off user_id must be "
                "provided."
            )

        if sampling_config_name and context_class_to_sampling_rate:
            raise MonaInitializationException(
                "Only one sampling method can be used at a time. Either remove "
                "sampling_config_name or context_class_to_sampling_rate"
            )

        self._logger = get_logger()

        self.api_key = api_key
        self.secret = secret

        self.raise_export_exceptions = raise_export_exceptions
        self.raise_service_exceptions = raise_service_exceptions
        self.should_log_failed_messages = should_log_failed_messages
        self.should_use_ssl = should_use_ssl
        self.should_use_authentication = should_use_authentication

        if should_use_authentication:
            self.raise_authentication_exceptions = raise_authentication_exceptions
            self.num_of_retries_for_authentication = num_of_retries_for_authentication
            self.wait_time_for_authentication_retries = (
                wait_time_for_authentication_retries
            )

            could_authenticate = first_authentication(self)
            if not could_authenticate:
                # TODO(anat): consider replacing this return with an if statement for
                #  the next part.
                return

        # If user_id=None then should_use_authentication must be True, which means at
        # this point the client was successfully authenticated and self._get_user_id()
        # will work.
        self._user_id = user_id or self._get_user_id()
        self._rest_api_url = (
            override_rest_api_full_url
            or self._get_rest_api_export_url(override_host=override_rest_api_host)
        )
        self._app_server_url = self._get_app_server_url(
            override_host=override_app_server_host
        )
        self.filter_none_fields_on_export = filter_none_fields_on_export

        # Data sampling.

        self._sampling_config_name = sampling_config_name
        self._context_class_to_sampling_rate = context_class_to_sampling_rate or {}
        self._default_sampling_rate = default_sampling_rate

        if self._sampling_config_name:
            sampling_factors_list = self.get_sampling_factors()

            if not sampling_factors_list:
                raise MonaInitializationException("Config name does not exist.")

            self._latest_seen_sampling_config = sampling_factors_list[0]

            self._context_class_to_sampling_rate = (
                self._latest_seen_sampling_config.get("factors_map", {})
            )
            self._default_sampling_rate = self._latest_seen_sampling_config.get(
                "default_factor", default_sampling_rate
            )

    def _get_rest_api_export_url(self, override_host=None):
        http_protocol = "https" if self.should_use_ssl else "http"
        host_name = override_host or f"incoming{self._user_id}.monalabs.io"
        endpoint_name = "export" if self.should_use_authentication else "monaExport"
        return f"{http_protocol}://{host_name}/{endpoint_name}"

    def _get_app_server_url(self, override_host=None):
        http_protocol = "https" if self.should_use_ssl else "http"
        host_name = override_host or f"api{self._user_id}.monalabs.io"
        return f"{http_protocol}://{host_name}"

    def is_active(self):
        """
        Returns True if the client is authenticated (or able to re-authenticate when
        needed) and therefore can export messages, otherwise returns False, meaning the
        client cannot export data to Mona's servers.
        Use this method to check client status in case RAISE_AUTHENTICATION_EXCEPTIONS
        is set to False.
        """
        return (
            is_authenticated(self.api_key) if self.should_use_authentication else True
        )

    def _get_user_id(self):
        """
        :return: The customer's user id (tenant id).
        """
        decoded_token = jwt.decode(
            get_current_token_by_api_key(self.api_key), verify=False
        )
        return decoded_token["tenantId"]

    @staticmethod
    def _filter_none_fields(message):
        return {key: val for key, val in message.items() if val is not None}

    def _should_filter_none_fields(self, filter_none_fields):
        """
        :param filter_none_fields:
            The value the export function got for filter_none_fields.
        :return: boolean
            True if the None fields should be filtered, if the caller function did
            not provide filter_none_fields use the client's self default.
        """
        return (
            self.filter_none_fields_on_export
            if filter_none_fields is None
            else filter_none_fields
        )

    @Decorators.refresh_token_if_needed
    def export(self, message: MonaSingleMessage, filter_none_fields=None):
        """
        Exports a single message to Mona's systems.

        :param message: MonaSingleMessage (required)
            message should be a MonaSingleMessage instance, which is a dataclass
            provided in this module.
        :param filter_none_fields: boolean (optional)
            When set to true fields with None values will be filtered out from the
            message dict.
        :return: boolean
            True if the message was successfully sent to Mona's systems,
            False otherwise (failure reason will be logged).
        """
        export_result = self._export_batch_inner(
            [message], filter_none_fields=filter_none_fields
        )
        return export_result and export_result["failed"] == 0

    @Decorators.refresh_token_if_needed
    def export_batch(
        self,
        events: List[MonaSingleMessage],
        default_action=None,
        filter_none_fields=None,
    ):
        """
        Use this function to easily send a batch of MonaSingleMessage to Mona.
        :param events: List[MonaSingleMessage] (required)
            Events should be a list of MonaSingleMessage (provided in this module).
        :param default_action: str (optional)
            The default action to the batch. Will be set as the action of all messages
            with no action provided.
        :param filter_none_fields: boolean (optional)
            When set to true fields with None values will be filtered out from the
            message dict.
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
        return self._export_batch_inner(
            events, default_action, filter_none_fields=filter_none_fields
        )

    def _should_add_message_to_sampled_data(self, message):
        context_class = message.get(CONTEXT_CLASS_FIELD_NAME)
        context_class_sampling_rate = self._context_class_to_sampling_rate.get(
            context_class
        )
        context_id = message.get(CONTEXT_ID_FIELD_NAME)
        if context_class_sampling_rate is not None:
            return keep_message_after_sampling(context_id, context_class_sampling_rate)
        return keep_message_after_sampling(context_id, self._default_sampling_rate)

    def _should_sample_data(self):
        return (self._default_sampling_rate < 1) or self._context_class_to_sampling_rate

    def _export_batch_inner(
        self,
        events: List[MonaSingleMessage],
        default_action=None,
        filter_none_fields=None,
    ):
        self._update_sampling_factors_if_needed()

        events = mona_messages_to_dicts_validation(
            events, self.raise_export_exceptions, self.should_log_failed_messages
        )
        if not events:
            return False

        messages_to_send = []
        for message_event in events:
            if not validate_mona_single_message(message_event):
                return handle_export_error(
                    error_message=(
                        "Messages to export must be of MonaSingleMessage type."
                    ),
                    should_raise_exception=self.raise_export_exceptions,
                    failed_message=events if self.should_log_failed_messages else None,
                )

            message_copy = dict(message_event)

            # TODO(anat): remove the following line once REST-api allows "contextClass"
            #  instead of "arcClass".
            message_copy[CONTEXT_CLASS_FIELD_NAME] = message_copy.pop("contextClass")

            # TODO(anat): Add full validations on client side.
            if validate_inner_message_type(message_copy["message"]):
                # Change fields in message that starts with "MONA_".
                message_copy["message"] = update_mona_fields_names(
                    message_copy["message"]
                )

            if (
                self._should_sample_data()
                and not self._should_add_message_to_sampled_data(message_copy)
            ):
                logging.info(
                    f"This event isn't a part of the sampled data: {message_event}"
                )
                continue

            if self._should_filter_none_fields(filter_none_fields):
                message_copy["message"] = self._filter_none_fields(
                    message_copy["message"]
                )
            # If the message was left empty after it was filtered, we don't want it to
            # be added.
            if message_copy["message"]:
                messages_to_send.append(message_copy)

        # Create and send the rest call to Mona's rest-api.
        try:
            if messages_to_send:
                rest_api_response = self._send_mona_rest_api_request(
                    messages_to_send, default_action, self._sampling_config_name
                )
            else:
                rest_api_response = None

        except ConnectionError:
            return handle_export_error(
                "Cannot connect to rest-api",
                self.raise_export_exceptions,
                events if self.should_log_failed_messages else None,
            )

        # Create the response and return it.
        client_response = Client._create_client_response(
            rest_api_response,
            total=len(messages_to_send),
        )
        if client_response["failed"] > 0:
            handle_export_error(
                f"Some messages didn't pass validation: {client_response}."
                f"{self._get_unauthenticated_mode_error_message()}",
                self.raise_export_exceptions,
                events if self.should_log_failed_messages else None,
            )

        else:
            if client_response["total"] > 0:
                self._logger.info(
                    f"All {client_response['total']} messages have been sent."
                )
            else:
                self._logger.info("No messages were sampled in this batch.")

        return client_response

    def _send_mona_rest_api_request(
        self, messages, default_action=None, sample_config_name=None
    ):
        """
        Sends a REST call to Mona's servers with the provided messages.
        :return: A REST response.
        """
        body = {
            "userId": self._user_id,
            "messages": messages,
        }
        if default_action:
            body["defaultAction"] = default_action

        if sample_config_name:
            body["sampleConfigName"] = sample_config_name

        return requests.request(
            "POST",
            self._rest_api_url,
            headers=get_basic_auth_header(self.api_key, self.should_use_authentication),
            json=body,
        )

    @staticmethod
    def _create_client_response(
        response,
        total,
    ):
        """
        Creates the dict response of the client to an export_batch() or export() call.
        :param response: The response received from the rest-api.
        :param total: total messages in batch.
        :return: A dict with response details (see export_batch docs for format).
        """
        # Sum the number of messaged that Mona's client didn't send to rest-api.
        failed = 0
        failure_reasons = {}

        # Check if some/all messages didn't passed validation on the rest-api.
        if total > 0 and not response.ok:
            try:
                result_info = response.json()
                # TODO(michal): Canonize incoming server responses.
                # Check for topLevelError in the response (returned when the request
                # fails for bad arguments).
                top_level_error = result_info.get("topLevelError")
                if top_level_error:
                    failure_reasons = top_level_error
                    failed = total

                # Other bad responses should have the following keys.
                else:
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
    def upload_config(self, config, commit_message, author=None):
        """
        Uploads a new configuration, as a json-serializable dict.
        The configuration file enables you to define how the exported data should be
        aggregated and analyzed in Mona, as well as your insight and alerting
        preferences.
        Find more information on creating your configuration at:
        https://docs.monalabs.io/.
        :param config: (dict) Your new Mona configuration represented as a python dict
        (both the configuration dict with your user_id as the top key and just the
        configuration dict itself are accepted).
        :param commit_message: (str)
        :param author: (str) An email address identifying the configuration uploader.
        Mona will use this mail to send updates regarding re-creation of insights upon
        this configuration change. When not supplied, the author will be the Client's
        api-key and you will not get updates regarding the changes mentioned above.
        Must be provided when using un-authenticated mode.
        :return: A dict holding the upload data:
        {
            "success": <was the upload successful>, (bool)
            "new_config_id": <the new configuration ID> (str)
        }
        """
        if not author and not self.should_use_authentication:
            return self._handle_service_error(
                "When using non authenticated client, author must be provided. "
            )

        if not isinstance(config, dict):
            return self._handle_service_error(CONFIG_MUST_BE_A_DICT_ERROR_MESSAGE)

        keys_list = list(config.keys())
        if len(keys_list) == 1 and keys_list[0] == self._user_id:
            config = config[keys_list[0]]

        config_to_upload = {
            "config": {self._user_id: config},
            "author": author or self.api_key,
            "commit_message": commit_message,
            "user_id": self._user_id,
        }

        upload_response = self._app_server_request("upload_config", config_to_upload)

        return (
            get_dict_result(
                False,
                None,
                upload_response["error_message"],
            )
            if "error_message" in upload_response
            else get_dict_result(True, upload_response["response_data"], None)
        )

    @Decorators.refresh_token_if_needed
    def upload_config_per_context_class(
        self, author, commit_message, context_class, config
    ):
        """
        A wrapper function for "Upload Config per Context Class" REST endpoint. view
        full documentation here:
        https://docs.monalabs.io/docs/upload-config-per-context-class-via-rest-api
        """
        app_server_response = self._app_server_request(
            "upload_config_for_context_class",
            data={
                "author": author,
                "commit_message": commit_message,
                "context_class": context_class,
                "config": config,
            },
        )
        return (
            app_server_response
            if "error_message" in app_server_response
            else get_dict_result(True, app_server_response["response_data"], None)
        )

    @Decorators.refresh_token_if_needed
    def get_config(self):
        """
        :return: A json-serializable dict with the current defined configuration.
        """
        app_server_response = self._app_server_request("configs")
        try:
            app_server_response = {
                self._user_id: app_server_response["response_data"][
                    "raw_configuration_data"
                ]
            }
            return get_dict_result(True, app_server_response, None)
        except KeyError:
            return self._handle_service_error(SERVICE_ERROR_MESSAGE)

    @Decorators.refresh_token_if_needed
    def get_suggested_config(self):
        """
        A wrapper function for "Retrieve Suggested Config" REST endpoint. view full
        documentation here:
        https://docs.monalabs.io/docs/retrieve-suggested-config-via-rest-api
        """
        app_server_response = self._app_server_request("get_new_config_fields")
        try:
            data = app_server_response["response_data"]["suggested_config"]
            return get_dict_result(True, data, None)
        except KeyError:
            return self._handle_service_error(SERVICE_ERROR_MESSAGE)

    @Decorators.refresh_token_if_needed
    def get_config_history(self, number_of_revisions=UNPROVIDED_VALUE):
        """
        A wrapper function for "Retrieve Config History" REST endpoint. view full
        documentation here:
        https://docs.monalabs.io/docs/retrieve-config-history-via-rest-api
        """
        app_server_response = self._app_server_request("get_config_history")

        return (
            get_dict_result(
                True,
                {
                    app_server_response["msg"]: app_server_response["configs"],
                    "number_of_revisions": number_of_revisions,
                },
                None,
            )
            if app_server_response.get("msg") is not None
            else self._handle_service_error(RETRIEVE_CONFIG_HISTORY_ERROR_MESSAGE)
        )

    @cached(cache=TTLCache(maxsize=100, ttl=SAMPLING_FACTORS_MAX_AGE_SECONDS))
    def _update_sampling_factors_if_needed(self):
        """
        If the client was initiated with a sampling config name, check if the
        configuration was changed since the client vars were assigned, and if so, update
        them accordingly.
        """
        if not self._sampling_config_name:
            return

        # Refetch the updated config from the index.
        sampling_config = self.get_sampling_factors()[0]

        if self._latest_seen_sampling_config == sampling_config:
            return

        self._latest_seen_sampling_config = sampling_config
        default_from_index = sampling_config.get("default_factor")
        factors_map_from_index = sampling_config.get("factors_map")

        if (
            default_from_index is not None
            and default_from_index != self._default_sampling_rate
        ):
            logging.info(
                f"The default sampling factor was updated: {default_from_index}"
            )
            self._default_sampling_rate = default_from_index

        if (
            factors_map_from_index
            and factors_map_from_index != self._context_class_to_sampling_rate
        ):
            logging.info(
                f"The sampling factors map was updated: {factors_map_from_index}"
            )
            self._context_class_to_sampling_rate = factors_map_from_index

    @Decorators.refresh_token_if_needed
    def get_sampling_factors(self):
        """
        A wrapper function for "Get sampling factors" REST endpoint.
        The response will include a list of sampling config names, with their sampling
        map and default sampling factor, in the following format:
        [{
            "config_name": "Training",
            "factors_map": {
                "TEST_CONTEXT_CLASS": 0.5,
            },
            "default_factor": 0.1,
        }]
        config_name is a required field, factors_map and default_factor are optional.
        When the client is initiated with a config name, only the matching config
        details will be returned (if exists).
        """
        app_server_response = self._app_server_request(
            "get_sampling_factors",
            data={"config_name": self._sampling_config_name},
        )

        error_message = app_server_response.get("error_message")
        return (
            self._handle_service_error(error_message)
            if error_message
            else get_dict_result(True, app_server_response["response_data"], None)
        )

    @Decorators.refresh_token_if_needed
    def create_sampling_factor(self, config_name, sampling_factor, context_class=None):
        """
        A wrapper function for "Create sampling factor" REST endpoint.
        """
        app_server_response = self._app_server_request(
            "create_sampling_factor",
            data={
                "config_name": config_name,
                "sampling_factor": sampling_factor,
                "context_class": context_class,
            },
        )
        error_message = app_server_response.get("error_message")

        return (
            self._handle_service_error(error_message)
            if error_message
            else get_dict_result(
                True,
                True,
                None,
            )
        )

    @Decorators.refresh_token_if_needed
    def validate_config(
        self,
        config,
        list_of_context_ids=UNPROVIDED_VALUE,
        latest_amount=UNPROVIDED_VALUE,
    ):
        """
        A wrapper function for "Validate Config" REST endpoint. View full documentation
        here: https://docs.monalabs.io/docs/validate-config-via-rest-api
        """
        app_server_response = self._app_server_request(
            "validate_config",
            data={
                "config": config,
                "list_of_context_ids": list_of_context_ids,
                "latest_amount": latest_amount,
            },
        )
        error_message = app_server_response.get("error_message")
        if error_message:
            return self._handle_service_error(error_message)

        app_server_response = app_server_response.get("response_data")

        return (
            self._handle_service_error(json.dumps(app_server_response.get("issues")))
            if app_server_response and "issues" in app_server_response
            else get_dict_result(True, app_server_response, None)
        )

    @Decorators.refresh_token_if_needed
    def validate_config_per_context_class(
        self,
        config,
        context_class,
        list_of_context_ids=UNPROVIDED_VALUE,
        latest_amount=UNPROVIDED_VALUE,
    ):
        """
        A wrapper function for "Validate Config Per Context Class" REST endpoint.
        View full documentation here:
        https://docs.monalabs.io/docs/validate-config-per-context-class-via-rest-api
        """
        app_server_response = self._app_server_request(
            "validate_config_per_context_class",
            data={
                "user_id": self._user_id,
                "config": config,
                "context_class": context_class,
                "list_of_context_ids": list_of_context_ids,
                "latest_amount": latest_amount,
            },
        )
        error_message = app_server_response.get("error_message")

        if error_message:
            return self._handle_service_error(error_message)

        return (
            self._handle_service_error(json.dumps(app_server_response.get("issues")))
            if app_server_response and "issues" in app_server_response
            else get_dict_result(True, app_server_response, None)
        )

    @Decorators.refresh_token_if_needed
    def get_insights(
        self,
        context_class,
        min_segment_size,
        insight_types=UNPROVIDED_VALUE,
        metric_name=UNPROVIDED_VALUE,
        min_insight_score=UNPROVIDED_VALUE,
        time_range_seconds=UNPROVIDED_VALUE,
        first_discovered_on_range_seconds=UNPROVIDED_VALUE,
    ):
        """
        A wrapper function for "Retrieve Insights" REST endpoint. view full
        documentation here:
        https://docs.monalabs.io/docs/retrieve-insights-using-the-rest-api
        """
        app_server_response = self._app_server_request(
            "insights",
            data={
                "context_class": context_class,
                "min_segment_size": min_segment_size,
                "insight_types": insight_types,
                "metric_name": metric_name,
                "min_insight_score": min_insight_score,
                "time_range_seconds": time_range_seconds,
                "first_discovered_on_range_seconds": first_discovered_on_range_seconds,
            },
        )

        return (
            self._handle_service_error(app_server_response["error_message"])
            if "error_message" in app_server_response
            else get_dict_result(True, app_server_response["response_data"], None)
        )

    @Decorators.refresh_token_if_needed
    def get_ingested_data_for_a_specific_segment(
        self,
        context_class,
        start_time,
        end_time,
        segment,
        sampling_threshold=UNPROVIDED_VALUE,
        excluded_segments=UNPROVIDED_VALUE,
    ):
        """
        A wrapper function for "Retrieve Ingested Data for a Specific Segment" REST
        endpoint. view full documentation here:
        https://docs.monalabs.io/docs/retrieve-ingested-data-for-a-specific-segment-via-rest-api
        """
        app_server_response = self._app_server_request(
            "get_ingested_data",
            data={
                "context_class": context_class,
                "start_time": start_time,
                "end_time": end_time,
                "segment": segment,
                "excluded_segments": excluded_segments,
                "sampling_threshold": sampling_threshold,
            },
        )

        return (
            self._handle_service_error(app_server_response["error_message"])
            if "error_message" in app_server_response
            # return the CRC's of the segment itself
            else get_dict_result(
                True, app_server_response["response_data"]["crcs"], None
            )
        )

    @Decorators.refresh_token_if_needed
    def get_suggested_config_from_user_input(self, events):
        """
        A wrapper function for "Retrieve Suggested Config from User Input" REST
        endpoint. view full documentation here:
        https://docs.monalabs.io/docs/retrieve-suggested-config-from-user-input-via-rest-api
        """
        app_server_response = self._app_server_request(
            "suggest_new_config",
            data={"events": events},
        )

        try:
            data = app_server_response["response_data"]["suggested_config"]
            return get_dict_result(True, data, None)
        except KeyError:
            return self._handle_service_error(SERVICE_ERROR_MESSAGE)

    @Decorators.refresh_token_if_needed
    def get_aggregated_data_of_a_specific_segment(
        self,
        context_class,
        timestamp_from,
        timestamp_to,
        time_series_resolutions=UNPROVIDED_VALUE,
        with_histogram=UNPROVIDED_VALUE,
        time_zone=UNPROVIDED_VALUE,
        metrics=UNPROVIDED_VALUE,
        requested_segments=UNPROVIDED_VALUE,
        excluded_segments=UNPROVIDED_VALUE,
        baseline_segment=UNPROVIDED_VALUE,
    ):
        """
        A wrapper function for "Retrieve Aggregated Data of a Specific Segment" REST
        endpoint. view full documentation here:
        https://docs.monalabs.io/docs/retrieve-aggregated-data-of-a-specific-segment-via-rest-api
        """
        app_server_response = self._app_server_request(
            "get_segment",
            data={
                "context_class": context_class,
                "timestamp_from": timestamp_from,
                "timestamp_to": timestamp_to,
                "time_series_resolutions": time_series_resolutions,
                "with_histogram": with_histogram,
                "time_zone": time_zone,
                "metrics": metrics,
                "requested_segments": requested_segments,
                "excluded_segments": excluded_segments,
                "baseline_segment": baseline_segment,
            },
        )
        return (
            app_server_response
            if "error_message" in app_server_response
            else get_dict_result(
                True,
                {"aggregated_data": app_server_response["response_data"]},
                None,
            )
        )

    @Decorators.refresh_token_if_needed
    def get_aggregated_stats_of_a_specific_segmentation(
        self,
        context_class,
        dimension,
        target_time_range,
        compared_time_range,
        metric_1_field,
        metric_2_field,
        metric_1_type,
        metric_2_type,
        min_segment_size,
        sort_function,
        baseline_segment=UNPROVIDED_VALUE,
        excluded_segments=UNPROVIDED_VALUE,
        target_segments_filter=UNPROVIDED_VALUE,
        compared_segments_filter=UNPROVIDED_VALUE,
    ):
        """
        A wrapper function for "Retrieve Aggregated Stats of Specific Segmentation" REST
        endpoint. view full documentation here:
        https://docs.monalabs.io/docs/retrieve-stats-of-specific-segmentation-via-rest-api
        """
        app_server_response = self._app_server_request(
            "stats",
            data={
                "context_class": context_class,
                "dimension": dimension,
                "target_time_range": target_time_range,
                "compared_time_range": compared_time_range,
                "metric_1_field": metric_1_field,
                "metric_2_field": metric_2_field,
                "metric_1_type": metric_1_type,
                "metric_2_type": metric_2_type,
                "min_segment_size": min_segment_size,
                "sort_function": sort_function,
                "baseline_segment": baseline_segment,
                "excluded_segments": excluded_segments,
                "target_segments_filter": target_segments_filter,
                "compared_segments_filter": compared_segments_filter,
            },
        )

        return (
            app_server_response
            if "error_message" in app_server_response
            else get_dict_result(True, app_server_response["response_data"], None)
        )

    @Decorators.refresh_token_if_needed
    def create_openai_context_class(self, context_class, openai_api_type):
        """
        A wrapper function for "Create new openAI context class" REST endpoint. View
        full documentation here:
        https://docs.monalabs.io/docs/create-new-openai-context-class-via-rest-api
        """
        app_server_response = self._app_server_request(
            "create_openai_context_class",
            data={"context_class": context_class, "openai_api_type": openai_api_type},
        )

        return (
            app_server_response
            if "error_message" in app_server_response
            else get_dict_result(True, app_server_response["response_data"], None)
        )

    @Decorators.refresh_token_if_needed
    def initiate_csv_upload_request(
        self,
        file_path,
        context_class,
        context_id_field=None,
        export_timestamp_field=None,
    ):
        """
        A wrapper function for initiate_csv_upload_request REST endpoint. Available
        only in specific Mona environments.
        """

        def _get_client_error_message(json_response):
            issues = json_response.get("issues", "")
            error = json_response.get("error_message")
            return f"{error + ': ' if (error and issues) else ''}{issues}"

        def custom_bad_response_handler(json_response, status_code):
            if status_code == CLIENT_ERROR_RESPONSE_STATUS_CODE:
                error_message = _get_client_error_message(json_response)

            elif status_code == SERVER_ERROR_RESPONSE_STATUS_CODE:
                error_message = json_response.get("error_message")

            else:
                error_message = SERVICE_ERROR_MESSAGE

            return self._handle_service_error(error_message)

        return self._app_server_request(
            endpoint_name="initiate_csv_upload_request",
            custom_bad_response_handler=custom_bad_response_handler,
            data={
                "file_path": file_path,
                "context_class": context_class,
                "context_id_field": context_id_field,
                "export_timestamp_field": export_timestamp_field,
            },
        )

    def _handle_service_error(self, error_message):
        """
        Logs an error and raises MonaServiceException if RAISE_SERVICE_EXCEPTIONS is
        true, returns false otherwise.
        """
        error_message += self._get_unauthenticated_mode_error_message()

        self._logger.error(error_message)
        if self.raise_service_exceptions:
            raise MonaServiceException(error_message)
        return get_dict_result(False, None, error_message)

    def _get_unauthenticated_mode_error_message(self):
        """
        If should_use_authentication=False return an error message (suggesting
        should_use_authentication mode turned off might be the cause for the exception)
        and an empty string otherwise.
        """
        return (
            ""
            if self.should_use_authentication
            else UNAUTHENTICATED_CHECK_ERROR_MESSAGE
        )

    def _default_bad_response_handler(self, json_response, status_code):
        if (
            json_response
            and "response_data" in json_response
            and status_code == CLIENT_ERROR_RESPONSE_STATUS_CODE
        ):
            return self._handle_service_error(json_response["response_data"])

        return self._handle_service_error(SERVICE_ERROR_MESSAGE)

    def _app_server_request(
        self, endpoint_name, data=None, custom_bad_response_handler=None
    ):
        """
        Send a request to Mona's app-server given endpoint with the given data (should
        be a dict with the endpoint requested fields).
        """
        try:
            app_server_response = requests.post(
                f"{self._app_server_url}/{endpoint_name}",
                headers=get_basic_auth_header(
                    self.api_key, self.should_use_authentication
                ),
                # Remove keys with UNPROVIDED_FIELD values to avoid overriding
                # the default value on the endpoint itself.
                json=(remove_items_by_value(data, UNPROVIDED_VALUE) if data else {}),
            )
            json_response = app_server_response.json()
            if not app_server_response.ok:
                bad_response_handler = (
                    custom_bad_response_handler or self._default_bad_response_handler
                )

                return bad_response_handler(
                    json_response=json_response,
                    status_code=app_server_response.status_code,
                )

            return json_response

        except ConnectionError:
            return self._handle_service_error(APP_SERVER_CONNECTION_ERROR_MESSAGE)
        except JSONDecodeError:
            return self._handle_service_error(SERVICE_ERROR_MESSAGE)
