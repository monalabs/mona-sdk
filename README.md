# Mona Python SDK
<p align="center">
  <img src="https://github.com/monalabs/mona-sdk/blob/main/mona_logo.png?raw=true" alt="Mona's logo" width="220"/>
</p>


Mona’s SDK is a python based package which enables you to securely access 
Mona’s API and export your data to Mona directly from within your code, 
either message-by-message or as a batch.

## Installation
```
$ pip install mona_sdk
```

## Quick Start and Example

1. Install as described above.
2. Get an "admin"-roled API key and secret from 
   [your dashboard](https://dashboard.monalabs.io/admin "Team management").
3. Set environment variables as mentioned below.
4. Instrument code with Mona's client as seen below.

### Data exporting arguments:
We recommend you get acquainted with Mona's key concepts 
[in our docs](https://docs.monalabs.io/docs/concepts "Mona's concepts").

**MonaSingleMessage**: A dataclass wrapping all needed fields for a Mona data exporting 
message, containing the following:
- **contextClass**: (str) The name of the context class to which you are currently exporting data.
- **message**: (dict) A JSON-serializable dict containing all relevant monitoring information
  to send to Mona's servers.
- **contextId**: (str) A unique identifier for the current context instance.
  One can export multiple messages with the same context id and Mona would aggregate all 
  of these messages to one big message on its backend. If none is given, Mona will create 
  a random uuid for it. This is highly unrecommended - since it takes away the option to 
  update this data in the future.
- **exportTimestamp**: (int | str) This is the primary timestamp Mona will use when considering the 
  data being sent. It should be a date (ISO string, or a Unix time number) representing
  the time the message was created. If this field isn't provided, the message 
  exportTimestamp will be the time in which the exporting function was called.

```
from mona_sdk.client import Client, MonaSingleMessage
import time

api_key = <An API key is accessible in the admin page in your dashboard>
secret = <secret corresponding to the given api_key>

my_mona_client = Client(api_key, secret)

# One can send a single message to Mona's servers by calling export() with a 
# MonaSingleMessage object:
succeed_to_export = my_mona_client.export(MonaSingleMessage(
    message={'monitoring_information_1': '1', 'monitoring_information_2': '2'}, 
    contextClass='MY_CONTEXT_CLASS_NAME', 
    contextId='CONTEXT_INSTANCE_UNIQUE_ID', 
    exportTimestamp=time.time()
))

# Another option is to send a batch of messages to Mona using export_batch:
messages_batch_to_mona = []
for context_instance in my_data:
    messages_batch_to_mona.append(
            MonaSingleMessage(
                message=context_instance.relevant_monitoring_information,
                contextClass="MY_CONTEXT_CLASS_NAME",
                contextId=context_instance.unique_id,
                exportTimestamp=context_instance.timestamp,
            )
        )
        
export_result = my_mona_client.export_batch(messages_batch_to_mona)
```
### Uploading a new configuration
Mona's sdk provides a simple way to upload a new Mona configuration, using Client.upload_config():
```
# Note: no need to add your user_id as the key, just the configuration itself.
new_configuration = <Your new Mona configuration>
author = <Who is uploding the new configuration> # provide this field if you are using unauthenticated mode.
upload_result = my_client.upload_config(new_configuration, "My commit message", author)

# the return value format will be:
# upload_result == {
#    "success": <was the upload successful>, (bool)
#    "new_config_id": <the new configuration ID> (str)
#}
```
You can also receive your current Mona configuration:
```
my_current_mona_config = my_client.get_config()
```

## Environment variables

Mona uses several environment variables you can set as you prefer:
- MONA_SDK_RAISE_AUTHENTICATION_EXCEPTIONS - Set to true if you would like Mona's client to
  raise authentication related exceptions. When set to false and such an exception is met,
  every function call will return false.
  Use client.is_active() in order to check authentication status. (default value: False).
- MONA_SDK_RAISE_EXPORT_EXCEPTIONS - set to true if you would like Mona's client to
  raise export related exceptions. When set to false and an export (or part of it) fails,
  the failure reason will be logged (default value: False).
- MONA_SDK_RAISE_CONFIG_EXCEPTIONS - set to true if you would like Mona's client to
  raise config related exceptions. When set to false, and such an exception is met,
  the function will log an error and return false (default value: False).
- MONA_SDK_NUM_OF_RETRIES_FOR_AUTHENTICATION - Number of retries to authenticate in case 
  Mona's client unexpectedly cannot get an authentication response from the server
  (default value: 3).
- MONA_SDK_WAIT_TIME_FOR_AUTHENTICATION_RETRIES_SEC - Number of seconds to wait between 
  every authentication retry (default value: 2).
- MONA_SDK_SHOULD_LOG_FAILED_MESSAGES - When true, failed messages will be logged ("ERROR" level).
- MONA_SDK_OVERRIDE_REST_API_URL- When provided, all messages to mona's rest-api will use this address instead of the default 
  one.
- MONA_SDK_OVERRIDE_APP_SERVER_URL When provided, all configuration related calls to mona's servers will use this address instead
  of the default one.

Another way to control these behaviors is to pass the relevant arguments to the client 
constructor as follows (the environment variables are used as defaults for these arguments):
```
my_mona_client = Client(
    api_key,
    secret,
    raise_authentication_exceptions=True,
    raise_export_exceptions=True,
    raise_config_exceptions=True,
    num_of_retries_for_authentication=6,
    wait_time_for_authentication_retries=0,
    should_log_failed_messages=True,
)
```

## Logging

Unrelated to the actual data being exported, Mona's client may log 
debug/info/warning/error for various reasons, including to help with debugging 
communications with Mona's server. To make logging as adaptable to your system 
as possible, Mona is using its own logger named "mona-logger". You can configure 
it in your code by just calling
```
logging.getLogger("mona-logger")
```

and then setting handlers and formatters as you please.

You can also configure Mona's logging using the following environment variables:

1. MONA_SDK_LOGGING_LEVEL - set this to the wanted level, according to python's logging
   constants:
   - "CRITICAL" (50)
   - "ERROR" (40)
   - "WARNING" (30)
   - "INFO" (20)
   - "DEBUG" (10)
   - "NOTSET" (0)
    
2. MONA_SDK_LOGGER_NAME - you can change Mona's logger name. 


## Special field names

Avoid using field names with "MONA" as their prefix, Mona uses this pattern internally. 
If you do that, these fields will be changed to a have prefix of "MY_MONA" before 
exporting to Mona's servers.

## Testing the client code

The client's tests are written using unittest framework.

In order to run the tests type the following to your shell:

```
python -m unittest mona_sdk/tests/client_tests.py
```