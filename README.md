# Mona Python SDK
<p style="text-align: center;">
  <img src="https://github.com/monalabs/mona-sdk/blob/main/mona_logo.png?raw=true" alt="Mona's logo" width="180"/>
</p>


Mona’s SDK is a python based package which enables you to securely access 
Mona’s API and send your data to Mona directly from within your code, 
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

### Data sending arguments:
We recommend you get acquainted with Mona's key concepts 
[in our docs](https://docs.monalabs.io/docs/concepts "Mona's concepts").

**MonaSingleMessage**: A dataclass wrapping all needed fields for a Mona data sending 
message, containing the following:
- **contextClass** (str): (Required) The name of the context class to which you are currently sending data.
- **message** (dict): (Required) A JSON-serializable dict containing all relevant monitoring information
  to send to Mona's servers.
- **contextId** (str): (Optional) A unique identifier for the current context instance.
  One can send multiple messages with the same context id and Mona would aggregate all 
  of these messages to one big message on its backend. If none is given, Mona will create 
  a random uuid for it. This is highly unrecommended - since it takes away the option to 
  update this data in the future.
- **sendTimestamp** (int | str): (Optional) This is the primary timestamp Mona will use when considering the 
  data being sent. It should be a date (ISO string, or a Unix time number) representing
  the time the message was created. If this field isn't provided, the message 
  sendTimestamp will be the time in which the sending function was called.
- **action** (str): (Optional) The action Mona should do with the message to an existing context:
  - "OVERWRITE": (default) The values in the given fields will replace values already existing in the given fields.
  - "ADD": The values in the given fields will be added to the values already existing in these fields (will be 
    eventually treated as arrays of values).
  - "NEW": completely reset the entire record of the given context id to only refer to the given message, so everything before
    this message is no longer relevant.
  
```
from mona_sdk.client import Client, MonaSingleMessage
import time

api_key = <An API key is accessible in the admin page in your dashboard>
secret = <secret corresponding to the given api_key>

my_mona_client = Client(api_key, secret)

# One can send a single message to Mona's servers by calling send_evnet() with a 
# MonaSingleMessage object:
succeed_to_send = my_mona_client.send_event(MonaSingleMessage(
    message={'monitoring_information_1': '1', 'monitoring_information_2': '2'}, 
    contextClass='MY_CONTEXT_CLASS_NAME', 
    contextId='CONTEXT_INSTANCE_UNIQUE_ID', 
    sendTimestamp=time.time(),
    action="OVERWRITE"
))

# Another option is to send a batch of messages to Mona using send_events_batch:
messages_batch_to_mona = []
for context_instance in my_data:
    messages_batch_to_mona.append(
            MonaSingleMessage(
                message=context_instance.relevant_monitoring_information,
                contextClass="MY_CONTEXT_CLASS_NAME",
                contextId=context_instance.unique_id,
                sendTimestamp=context_instance.timestamp,
            )
        )
        
# Use dafault_action to select a default action for messages with no specified action.
send_result = my_mona_client.send_events_batch(
    messages_batch_to_mona, 
    default_action="ADD",
    )
```
## Mona SDK services
Mona sdk provides a simple API to access your information and control your configuration and data on Mona.
You can see all functions info and examples on [our docs](https://docs.monalabs.io/docs) under REST API.
Notice that the responses (since version 0.0.46) match the 'Service responses' section below, which is a 
bit different from the responses for the REST API.

### The available services are:

#### [get_config](https://docs.monalabs.io/docs/retrieve-current-config-file)
#### [get_suggested_config](https://docs.monalabs.io/docs/retrieve-suggested-config-via-rest-api)
#### [validate_config](https://docs.monalabs.io/docs/validate-config-via-rest-api)
#### [validate_config_per_context_class](https://docs.monalabs.io/docs/validate-config-per-context-class-via-rest-api)
#### [upload_config](https://docs.monalabs.io/docs/upload-config-via-rest)
#### [upload_config_per_context_class](https://docs.monalabs.io/docs/upload-config-per-context-class-via-rest-api)
#### [get_config_history](https://docs.monalabs.io/docs/retrieve-config-history-via-rest-api)
#### [get_insights](https://docs.monalabs.io/docs/retrieve-insights-using-the-rest-api)
#### [get_ingested_data_for_a_specific_segment](https://docs.monalabs.io/docs/retrieve-ingested-data-for-a-specific-segment-via-rest-api)
#### [get_suggested_config_from_user_input](https://docs.monalabs.io/docs/retrieve-suggested-config-from-user-input-via-rest-api)
#### [get_aggregated_data_of_a_specific_segment](https://docs.monalabs.io/docs/retrieve-aggregated-data-of-a-specific-segment-via-rest-api)
#### [get_aggregated_stats_of_a_specific_segmentation](https://docs.monalabs.io/docs/retrieve-stats-of-specific-segmentation-via-rest-api)
#### [create_openai_context_class](https://docs.monalabs.io/docs/create-new-openai-context-class-via-rest-api)


#### Service response:
The structure of the response for the different services is as follows:
```
{
    "success": <was the request successful>, (bool)
    "data": <the returned response data> (str|dict|list|None)
    "error_message": <explains the error, if occured> (str)
}
```

#### Example - upload a new configuration:

Arguments:
    
- **config**: Your new Mona [configuration](https://docs.monalabs.io/docs/configuration-overview) represented as a 
  python dict (both the configuration dict with your user_id as the top key and just the configuration dict itself are 
  accepted).
- **commit_message**: A short description of the changes that were made.
- **author**: An email address identifying the configuration uploader. Mona will use this mail to send updates regarding
  re-creation of insights upon this configuration change. When not supplied, the author will be the Client's api-key, 
  and you will not get updates regarding the changes mentioned above. Must be provided when using un-authenticated mode.
```
new_configuration = {
    "MY_CONTEXT_CLASS": {
        "fields": <fields dict>, 
        "field_vectors": <field vectors dict>
        "stanzas_global_defaults": <global defaults dict>, 
        "stanzas": <stansas dict>,
        "notifications": <notifications dict>
    }
}
author = 'author@mycompany.io'
upload_result = my_client.upload_config(new_configuration, "My commit message", author)

# the return value format will be:
# upload_result == {
#    "success": <was the upload successful>, (bool)
#    "data": {"new_config_id": <the new configuration ID> (str), "new_config":<the config that was uploaded> (dict)}
#    "error_message": <explains the error, if occured> (str)
#}
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
- MONA_SDK_RAISE_SERVICE_EXCEPTIONS - set to true if you would like Mona's client to
  raise services requests related exceptions (see all available services under [Mona SDK services](#mona-sdk-services) 
  section in this doc). When set to false, and such an exception is met,
  the function will log an error and return false (default value: False).
- MONA_SDK_NUM_OF_RETRIES_FOR_AUTHENTICATION - Number of retries to authenticate in case 
  Mona's client unexpectedly cannot get an authentication response from the server
  (default value: 3).
- MONA_SDK_WAIT_TIME_FOR_AUTHENTICATION_RETRIES_SEC - Number of seconds to wait between 
  every authentication retry (default value: 2).
- MONA_SDK_SHOULD_LOG_FAILED_MESSAGES - When true, failed messages will be logged ("ERROR" level).
- MONA_SDK_OVERRIDE_APP_SERVER_HOST - When provided, all configuration related calls to mona's servers will use this 
  host name instead of the default one ("api<user_id>.monalabs.io").
- MONA_SDK_OVERRIDE_APP_SERVER_URL - When provided, all messages to Mona's servers will use this full url address 
  (including "http" prefix and endpoints suffix) instead of the default one.
- MONA_SDK_OVERRIDE_REST_API_HOST- When provided, all messages (data export) to mona's rest-api will use this host 
  address instead of the default one ("incoming<user_id>.monalabs.io").
- MONA_SDK_OVERRIDE_REST_API_URL- When provided, all messages to mona's rest-api will use this full url address 
  (including "http" prefix and endpoints suffix) instead of the default one. 
  **Note**: this is mostly for internal use, please use MONA_SDK_OVERRIDE_REST_API_HOST if needed.
- MONA_SDK_SHOULD_USE_SSL - Should the communication with Mona's servers be with (https) or without (http) ssl 
  (default value: True).
- MONA_SDK_SHOULD_USE_AUTHENTICATION - When set to false, the communication with Mona's servers will not use 
  authentication (user_id should be provided to the Client constructor instead of an api_key and a secret), **Note**: 
  this mode is not supported on the servers by default, and must be explicitly requested from Mona's team (default 
  value: True).
- MONA_SDK_FILTER_NONE_FIELDS_ON_EXPORT - When set to true, Mona's client will filter out all fields with None values 
  from the message dict to export (default value: False). Note that passing a None value may be required in order to delete a pre-existing 
  value. To allow None values, use filter_none_fields=False which overrides this parameter both in export() and 
  export_batch() functions.
- MONA_SDK_DEFAULT_SAMPLING_FACTOR - A float in the range [0, 1], which sets the random client-side sampling done by the SDK before sending the data into Mona servers. If this value is less than 1, only a random (see below) sample of the given proportion is actually going to be sent, leaving the rest of the data unattended. Use with caution. (random - using hashing with sha224 on the context id, if supplied, or by random.random() otherwise.)
- MONA_SDK_SAMPLING_CONFIG - Allows to override the sampling factor (see MONA_SDK_DEFAULT_SAMPLING_FACTOR above) by context class. If set, the expected format is a *valid* JSON-object string. Keys are the names of the context classes to override, and the value is expected to be floats in the range of [0, 1]. For example: '{"class1": 0.3, "class2": 0.5, "class3": 1}'

Another way to control these behaviors is to pass the relevant arguments to the client 
constructor as follows (the environment variables are used as defaults for these arguments, and by passing these 
arguments to the constructor you can override the default values you set with the environment variables):
```
my_mona_client = Client(
    api_key,
    secret,
    raise_authentication_exceptions=True,
    raise_export_exceptions=True,
    raise_service_exceptions=True,
    num_of_retries_for_authentication=6,
    wait_time_for_authentication_retries=0,
    should_log_failed_messages=True,
    filter_none_fields_on_export=True,
    default_sampling_rate=0.1,
    context_class_to_sampling_rate={"class1": 0.5, "class2": 1},
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

## Asynchronous Client

Same services as the regular client are provided in a non-blocking version in the AsyncClient, in order to give you the option to embed the code you write using this package with asyncIO code.

**AsyncClient Constructor parameters:** 
  - event_loop (_UnixSelctorEventLoop): (optional) The event loop that will manage the threads. If not provided, a default is used.
  - executor (TreadPoolExecutor): (optional) The executor that will manage the thread pool. If not provided, a default is used.
  
  
When using AsyncClient, while all the regular (synchronous) client functions are still supported, you can simply add "_async" suffix to any function (e.g export_async() instead of export(); export_batch_async() instead of export_batch() etc). The async version of the methods accept the same parameters as the synchronous version, in addition to the following parameters:
  - event_loop (_UnixSelctorEventLoop): (optional) This overrides the event loop provided for the AsyncClient constructor. 
  - executor (TreadPoolExecutor): (optional) This overrides the executor provided for the AsyncClient constructor. 


**An example for using export_batch_async to send data to Mona asynchronously, and then printing the result and exception (if occurred)**:
```
from mona_sdk import MonaSingleMessage
from mona_sdk.async_client import AsyncClient
import asyncio

async def main():
    api_key = <An API key is accessible in the admin page in your dashboard>
    secret = <secret corresponding to the given api_key>

    my_mona_async_client = AsyncClient(api_key, secret)

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

    task = asyncio.create_task(my_mona_async_client.export_batch_async(messages_batch_to_mona))
    await task
    print(task.result())
    print(task.exception())
asyncio.run(main())
```
