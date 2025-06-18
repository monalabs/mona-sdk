import warnings
from dataclasses import dataclass
from os import environ

from mona_sdk.client_util import get_boolean_value_for_env_var

MONA_SDK_ENABLE_DEPRECATION_WARNINGS_ON_EXPORT_TIMESTAMP = (
    get_boolean_value_for_env_var(
        environ.get("MONA_SDK_ENABLE_DEPRECATION_WARNINGS_ON_EXPORT_TIMESTAMP"), False
    )
)


MONA_SDK_USE_SEND_TIMESTAMP_FIELD = get_boolean_value_for_env_var(
    environ.get("MONA_SDK_USE_SEND_TIMESTAMP_FIELD"), False
)


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
        :param sendTimestamp (int|str): (Optional) This is the primary timestamp Mona
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
        sendTimestamp=<the message export timestamp>,
        action=<the wanted action>
    )
    """

    message: dict
    contextClass: str
    contextId: str = None
    action: str = None
    sampleConfigName: str = None

    exportTimestamp: int or str = None
    sendTimestamp: int or str = None

    def __post_init__(self):
        if not MONA_SDK_USE_SEND_TIMESTAMP_FIELD:

            if self.exportTimestamp is None and self.sendTimestamp is not None:
                self.exportTimestamp = self.sendTimestamp
                del self.sendTimestamp

        else:

            if self.exportTimestamp is not None and self.sendTimestamp is None:
                self.sendTimestamp = self.exportTimestamp
                del self.exportTimestamp

                if MONA_SDK_ENABLE_DEPRECATION_WARNINGS_ON_EXPORT_TIMESTAMP:
                    warnings.warn(
                        "'exportTimestamp' is deprecated. Use 'sendTimestamp' instead.",
                        DeprecationWarning,
                        stacklevel=2,
                    )

    def get_dict(self):
        return {
            key: value
            for key, value in self.__dict__.items()
            if key in MonaSingleMessage.__dataclass_fields__.keys()
        }
