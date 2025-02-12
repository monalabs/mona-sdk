from dataclasses import dataclass


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
        action=<the wanted action>
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
