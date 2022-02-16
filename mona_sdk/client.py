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

from mona_sdk.client_exceptions import (
    MonaServiceException,
    MonaInitializationException,
)
from .client_util import get_boolean_value_for_env_var, remove_items_by_value
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

SERVICE_ERROR_MESSAGE = "Could not get server response for the wanted service."
UPLOAD_CONFIG_ERROR_MESSAGE = (
    "Could not upload the new configuration, please check it is valid."
)
APP_SERVER_CONNECTION_ERROR_MESSAGE = "Cannot connect to app-server."

UNAUTHENTICATED_ERROR_CHECK_MESSAGE = (
    "\nNotice that should_use_authentication is set to False, which is not supported by"
    " default and must be explicitly requested from Mona team."
)

# The argument to use as a default value on the values of the data argument (dict) when
# calling _app_server_request(). Use this and not None in order to be able to pass a
# None argument if needed.
UNPROVIDED_VALUE = "mona_unprovided_value"


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
                f"Some messages didn't pass validation: {client_response}."
                f"{self._get_unauthenticated_mode_error_message()}",
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
            headers=get_basic_auth_header(self.api_key, self.should_use_authentication),
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
        upload_output = {"success": False, "new_config_id": ""}

        if not author and not self.should_use_authentication:
            self._handle_service_error(
                "When using non authenticated client, author must be provided."
            )
            return upload_output

        if not isinstance(config, dict):
            self._handle_service_error("config must be a dict.")
            return upload_output

        keys_list = list(config.keys())
        if len(keys_list) == 1 and keys_list[0] == self._user_id:
            config = config[keys_list[0]]

        config_to_upload = {
            "config": {self._user_id: config},
            "author": author or self.api_key,
            "commit_message": commit_message,
            "user_id": self._user_id,
        }

        try:
            upload_response = requests.post(
                f"{self._app_server_url}/upload_config",
                headers=get_basic_auth_header(
                    self.api_key, self.should_use_authentication
                ),
                json=config_to_upload,
            )
            response_data = upload_response.json()["response_data"]
            upload_output["new_config_id"] = response_data["new_config_id"]
            upload_output["success"] = upload_response.ok

            if not upload_output["success"]:
                # Raise an exception if asked to.
                self._handle_service_error(UPLOAD_CONFIG_ERROR_MESSAGE)

        except ConnectionError:
            # Raise an exception if asked to.
            self._handle_service_error(APP_SERVER_CONNECTION_ERROR_MESSAGE)
        except JSONDecodeError:
            # Raise an exception if asked to.
            self._handle_service_error(UPLOAD_CONFIG_ERROR_MESSAGE)

        return upload_output

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
        if "response_data" not in app_server_response:
            self._handle_service_error(
                SERVICE_ERROR_MESSAGE + f" Service response: {app_server_response}"
            )

        return app_server_response

    @Decorators.refresh_token_if_needed
    def get_config(self):
        """
        :return: A json-serializable dict with the current defined configuration.
        """
        app_server_response = self._app_server_request("configs")
        try:
            return {
                self._user_id: app_server_response["response_data"][
                    "raw_configuration_data"
                ]
            }
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
            return app_server_response["response_data"]["suggested_config"]
        except KeyError:
            return self._handle_service_error(SERVICE_ERROR_MESSAGE)

    @Decorators.refresh_token_if_needed
    def get_config_history(self, number_of_revisions=UNPROVIDED_VALUE):
        """
        A wrapper function for "Retrieve Config History" REST endpoint. view full
        documentation here:
        https://docs.monalabs.io/docs/retrieve-config-history-via-rest-api
        """
        return self._app_server_request(
            "get_config_history", data={"number_of_revisions": number_of_revisions}
        )

    @Decorators.refresh_token_if_needed
    def validate_config(
        self,
        config,
        list_of_context_ids=UNPROVIDED_VALUE,
        latest_amount=UNPROVIDED_VALUE,
    ):
        """
        A wrapper function for "Validate Config" REST endpoint. view full documentation
        here: https://docs.monalabs.io/docs/validate-config-via-rest-api
        """
        return self._app_server_request(
            "validate_config",
            data={
                "config": config,
                "list_of_context_ids": list_of_context_ids,
                "latest_amount": latest_amount,
            },
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
        return self._app_server_request(
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

    @Decorators.refresh_token_if_needed
    def get_ingested_data_for_a_specific_segment(
        self,
        context_class,
        start_time,
        end_time,
        segment,
        excluded_segments=UNPROVIDED_VALUE,
    ):
        """
        A wrapper function for "Retrieve Ingested Data for a Specific Segment" REST
        endpoint. view full documentation here:
        https://docs.monalabs.io/docs/retrieve-ingested-data-for-a-specific-segment-via-rest-api
        """
        return self._app_server_request(
            "get_ingested_data",
            data={
                "context_class": context_class,
                "start_time": start_time,
                "end_time": end_time,
                "segment": segment,
                "excluded_segments": excluded_segments,
            },
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
        if "response_data" not in app_server_response:
            self._handle_service_error(SERVICE_ERROR_MESSAGE)

        return app_server_response

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
        return self._app_server_request(
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

        if "response_data" not in app_server_response:
            self._handle_service_error(
                f"{SERVICE_ERROR_MESSAGE} Server response: {app_server_response}"
            )

        return app_server_response

    def _handle_service_error(self, error_message):
        """
        Logs an error and raises MonaServiceException if RAISE_SERVICE_EXCEPTIONS is
        true, returns false otherwise.
        """
        error_message += self._get_unauthenticated_mode_error_message()

        self._logger.error(error_message)
        if self.raise_service_exceptions:
            raise MonaServiceException(error_message)
        return False

    def _get_unauthenticated_mode_error_message(self):
        """
        If should_use_authentication=False return an error message (suggesting
        should_use_authentication mode turned off might be the cause for the exception)
        and an empty string otherwise.
        """
        return (
            ""
            if self.should_use_authentication
            else UNAUTHENTICATED_ERROR_CHECK_MESSAGE
        )

    def _app_server_request(self, endpoint_name, data=None):
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
                # Remove keys with UNPROVIDED_FIELD values to avoid overriding the
                # default value on the endpoint itself.
                json=remove_items_by_value(data, UNPROVIDED_VALUE) if data else {},
            )
            json_response = app_server_response.json()
            if not app_server_response.ok:
                return self._handle_service_error(SERVICE_ERROR_MESSAGE)

            return json_response

        except ConnectionError:
            return self._handle_service_error(APP_SERVER_CONNECTION_ERROR_MESSAGE)
        except JSONDecodeError:
            return self._handle_service_error(SERVICE_ERROR_MESSAGE)
