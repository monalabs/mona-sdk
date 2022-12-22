from mona_sdk import Client

print("Starting test ...")

# Es monitor test
client_id = "39e981fe-919d-413c-8a1a-6a01a968fc99"
secret_key = "74f52ead-2f42-4773-8f3e-94ea9fbdf756"
user_id = "b5a50a81-3e77-4ab1-b06b-7f35d9d920fe"
context_class_name = "context_class"
context_class_name_chen = "context_class_chen"
context_class_name_loan = "LOAN_APPLICATION_TUTORIAL"

# Let's have 4 context classes - the 4th will take the default value (0.7).
my_mona_client = Client(
    api_key=client_id,
    secret=secret_key,
    user_id=user_id,
    raise_export_exceptions=True,
    should_use_ssl=False,
    override_app_server_host="127.0.0.1:5000"
    # raise_service_exceptions=True,
)

my_mona_client2 = Client(
    secret=secret_key,
    user_id=user_id,
    raise_export_exceptions=False,
    should_use_ssl=False,
    override_app_server_host="127.0.0.1:5000",
    raise_service_exceptions=False,
)

my_mona_client3 = Client(
    secret=secret_key,
    user_id=user_id,
    raise_export_exceptions=False,
    should_use_ssl=False,
    override_app_server_host="127.0.0.1:5000",
    raise_service_exceptions=False,
    should_use_authentication=False,
)

context_class_config_no_good = {
    "fields": {
        "number_of_something": {"type": "numeric"},
        "on_camera": {"type": "boolean"},
        "on_microphone": {"type": "boolean"},
        "another_numeric_source": {"type": "numeric"},
        "field_that_shouldnt_pass": {"type": "ahalan"},
    }
}

context_class_config_all_good = {
    "fields": {
        "number_of_something": {"type": "numeric"},
        "on_camera": {"type": "boolean"},
        "on_microphone": {"type": "boolean"},
        "another_numeric_source": {"type": "numeric"},
    }
}

context_class_config_all_good2 = {
    "fields": {
        "number_of_something": {"type": "numeric"},
        "on_camera": {"type": "boolean"},
        "on_microphone": {"type": "boolean"},
    }
}

context_class_config_identical = {
    "fields": {
        "number_of_something": {"type": "numeric"},
        "on_camera": {"type": "boolean"},
        "on_microphone": {"type": "boolean"},
    }
}

context_class_loan = {
    "fields": {
        "occupation": {
            "type": "string",
            "function": "identity",
            "args": [],
            "tags": ["metadata"],
        },
        "state": {"type": "string"},
        "purpose": {"type": "string"},
        "credit_score": {
            "type": "numeric",
            "function": "identity",
            "args": [],
            "segmentations": {"original": {"default": True, "bucket_size": 0.02}},
        },
    },
    "stanzas": {
        "general": {
            "description": "",
            "verses": [
                {
                    "type": "AverageDrift",
                    "metrics": [
                        "credit_score",
                        "offered_amount",
                        "approved_amount",
                        "credit_label_delta",
                        "offered_approved_delta_normalized",
                    ],
                    "segment_by": [
                        "occupation",
                        "purpose",
                        "stage",
                        "model_version",
                        {"name": "occupation", "avoid_values": ["doctor"]},
                    ],
                    "min_anomaly_level": 0.25,
                    "trend_directions": ["desc"],
                    "min_segment_size": 500,
                },
            ],
        }
    },
}


# print("---------Tests: upload_config- good-------------------------------------------")
config_good = {
    "b5a50a81-3e77-4ab1-b06b-7f35d9d920fe": {
        "context_class_name": {
            "fields": {
                "number_of_something": {"type": "numeric"},
                "on_camera": {"type": "boolean"},
                "on_microphone": {"type": "boolean"},
            }
        }
    }
}


config_loan = {
    "b5a50a81-3e77-4ab1-b06b-7f35d9d920fe": {
        "LOAN_APPLICATION_TUTORIAL": {
            "fields": {
                "occupation": {"type": "string"},
                "city": {"type": "string"},
                "state": {"type": "string"},
                "purpose": {"type": "string"},
                "credit_score": {
                    "type": "numeric",
                    "segmentations": {
                        "original": {"default": True, "bucket_size": 0.02}
                    },
                },
                "loan_taken": {"type": "boolean"},
                "return_until": {
                    "type": "numeric",
                    "segmentations": {
                        "original": {"default": True, "bucket_size": 1000000}
                    },
                },
                "offered_amount": {
                    "type": "numeric",
                    "segmentations": {
                        "original": {"default": True, "bucket_size": 700}
                    },
                },
                "approved_amount": {
                    "type": "numeric",
                    "segmentations": {
                        "original": {"default": True, "bucket_size": 700}
                    },
                },
                "feature_0": {
                    "type": "numeric",
                    "segmentations": {
                        "original": {"default": True, "bucket_size": 60000}
                    },
                },
                "feature_1": {
                    "type": "numeric",
                    "segmentations": {
                        "original": {"default": True, "bucket_size": 0.4}
                    },
                },
                "feature_2": {
                    "type": "numeric",
                    "segmentations": {"original": {"default": True, "bucket_size": 30}},
                },
                "feature_3": {
                    "type": "numeric",
                    "segmentations": {
                        "original": {"default": True, "bucket_size": 6000}
                    },
                },
                "feature_4": {
                    "type": "numeric",
                    "segmentations": {
                        "original": {"default": True, "bucket_size": 0.01}
                    },
                },
                "feature_5": {
                    "type": "numeric",
                    "segmentations": {
                        "original": {"default": True, "bucket_size": 0.2}
                    },
                },
                "feature_6": {
                    "type": "numeric",
                    "segmentations": {"original": {"default": True, "bucket_size": 20}},
                },
                "feature_7": {
                    "type": "numeric",
                    "segmentations": {"original": {"default": True, "bucket_size": 1}},
                },
                "feature_8": {
                    "type": "numeric",
                    "segmentations": {"original": {"default": True, "bucket_size": 50}},
                },
                "feature_9": {
                    "type": "numeric",
                    "segmentations": {"original": {"default": True, "bucket_size": 20}},
                },
                "stage": {"type": "string"},
                "model_version": {"type": "string"},
                "loan_paid_back": {"type": "boolean"},
            }
        }
    }
}

# ret = my_mona_client.upload_config(
#     author="smadar@monalabs.io",
#     commit_message="test for config upload",
#     config=config_good,
# )
# print(ret)

# ret = my_mona_client.upload_config(
#     author="smadar@monalabs.io",
#     commit_message="test for config upload",
#     config=config_loan,
# )
# print(ret)


# print("---------Tests: upload_config- not good----------------------------------------")
config_no_good = {
    "b5a50a81-3e77-4ab1-b06b-7f35d9d920fe": {
        "context_class_name": {
            "fields": {
                "number_of_something": {"type": "numeric"},
                "field_that_shouldnt_pass": {"type": "ahadcdclan"},
            }
        }
    }
}

# ret = my_mona_client3.upload_config(
#     commit_message="test for config upload",
#     config=config_no_good,
# )
# print(ret)

# ret = my_mona_client3.upload_config("hi", commit_message="", author="hi")
# print(ret)

# ret = my_mona_client3.upload_config(
#     author="smadar@monalabs.io",
#     commit_message="test for config upload",
#     config=config_no_good,
# )
# print(ret)


# print("---------Tests: upload_config_per_context_class- good--------------------------")
# ret = my_mona_client.upload_config_per_context_class(
#     author="smadar@monalabs.io",
#     commit_message="test for cc config upload",
#     context_class=context_class_name,
#     config=context_class_config_all_good,
# )
# print(ret)


# ret = my_mona_client.upload_config_per_context_class(
#     author="chen+tutorial@monalabs.io",
#     commit_message="updated context class LOAN_APPLICATION_TUTORIAL",
#     context_class="LOAN_APPLICATION_TUTORIAL",
#     config=context_class_loan,
# )
# print(ret)

# ret = my_mona_client.upload_config_per_context_class(
#     author="smadar@monalabs.io",
#     commit_message="test for cc config upload",
#     context_class=context_class_name,
#     config=context_class_config_all_good2,
# )
# print(ret)

# ret = my_mona_client.upload_config_per_context_class(
#   author="smadar@monalabs.io",
#   commit_message="test for cc config upload",
#   context_class=context_class_name,
#   config=context_class_config_identical,
# )
# print(ret)

# print("---------Tests: sending upload_config_per_context_class- not good---------------")
# ret = my_mona_client.upload_config_per_context_class(
#    author="smadar@monalabs.io",
#    commit_message="test for cc config upload",
#    context_class=context_class_name,
#    config=context_class_config_no_good,
# )
# print(ret)

# print("---------Tests: get_sampling_factors- good----------------------------------------")
# sampling_factors = my_mona_client.get_sampling_factors()
# print(sampling_factors)

# print("---------Tests: get_sampling_factors- not good----------------------------------------")
# sampling_factors = my_mona_client2.get_sampling_factors()
# print(sampling_factors)

# print("---------Tests: get_suggested_config_from_user_input- good----------------------------------------")
events = {
    "userId": user_id,
    "messages": [
        {
            "arcClass": "arcClassName",
            "contextId": "ID_123",
            "message": {
                "company-id": "79sg7723-0253438g3453",
                "browser": "chrome",
                "text_length": 50,
                "top_tagged_brand": "adidas",
            },
        },
        {
            "arcClass": "arcClassName",
            "contextId": "ID_123",
            "message": {"coutry": "usa"},
        },
        {
            "arcClass": "arcClassName",
            "contextId": "ID_124",
            "message": {
                "company-id": "2435f32-02ve3538g5232",
                "browser": "safari",
                "text_length": 30,
                "top_tagged_brand": "nike",
            },
        },
    ],
}
# suggested_config = my_mona_client.get_suggested_config_from_user_input(events)
# print(suggested_config)


suggested_config = my_mona_client.get_suggested_config_from_user_input(
    events={
        "messages": [
            {
                "arcClass": "LOAN_APPLICATION_TUTORIAL",
                "contextId": "someContextId",
                "exportTimestamp": 1644466612,
                "message": {
                    "occupation": "manufacturing",
                    "city": "Fort Smith",
                    "state": "Arkansas",
                    "purpose": "Credit score improvement",
                    "credit_score": 0.3926368592424558,
                    "loan_taken": True,
                    "return_until": 1619948737000,
                    "offered_amount": 2015,
                    "approved_amount": 2015,
                    "stage": "inference",
                    "model_version": "v1",
                },
            },
            {
                "arcClass": "LOAN_APPLICATION_TUTORIAL",
                "contextId": "someContextId",
                "exportTimestamp": 1644488612,
                "message": {
                    "feature_0": 2858561.5949184396,
                    "feature_1": 5.777438394215511,
                    "feature_2": 762,
                    "feature_3": 8102,
                    "feature_4": 0,
                    "feature_5": 0.9689581447209208,
                    "feature_6": 27,
                    "feature_7": 0,
                    "feature_8": 1384.99655593255,
                    "feature_9": 18.11042489302702,
                },
            },
        ]
    }
)
# print(suggested_config)


# print("---------Tests: get_suggested_config_from_user_input- not good-----------------")
events_not_good = {
    "messages": [
        {
            "message": {
                "company-id": "79sg7723-0253438g3453",
                "browser": "chrome",
                "text_length": 50,
                "top_tagged_brand": "adidas",
            },
        },
        {
            "arcClass": "arcClassName",
            "message": {"coutry": "usa"},
        },
        {
            "arcClass": "arcClassName",
            "contextId": "ID_124",
            "company-id": "2435f32-02ve3538g5232",
            "browser": "safari",
            "text_length": 30,
            "top_tagged_brand": "nike",
        },
    ],
}
# suggested_config = my_mona_client.get_suggested_config_from_user_input(events_not_good)
# print(suggested_config)


# print("---------Tests: get_suggested_config- good--------------------------------------------")
# config = my_mona_client.get_suggested_config()
# print(config)


# print("-----Tests: get_aggregated_data_of_a_specific_segment not good----------------")
# res = my_mona_client.get_aggregated_data_of_a_specific_segment(
#     context_class=context_class_name_chen,
#     timestamp_from=0,
#     timestamp_to=16713399,
# )
# print(res)

# res = my_mona_client.get_aggregated_data_of_a_specific_segment(
#     context_class="context_class_name",
#     timestamp_from=0,
#     timestamp_to=17713399,
# )
# print(res)
# print("-----Tests: get_aggregated_data_of_a_specific_segmentgood----------------")

res = my_mona_client.get_aggregated_data_of_a_specific_segment(
    context_class="LOAN_APPLICATION_TUTORIAL",
    timestamp_to=1619616543,
    timestamp_from=1619098143,
    requested_segments=[{"occupation": [{"value": "retail"}]}],
    metrics=[{"field": "feature_1", "types": ["average"]}],
    time_series_resolutions=["1d"],
    with_histogram=True,
)
print(res)

# print("---------Tests: get_config- good--------------------------------------------")
# config = my_mona_client.get_config()
# print(config)

# print("---------Tests: get_config- not good---------------------------------------")
# config = my_mona_client2.get_config()
# print(config)

# print("---------Tests: validate_config- good-----------------------------------------")
# res = my_mona_client.validate_config(config_good)
# print(res)

# print("---------Tests: validate_config- not good-----------------------------------")
# res = my_mona_client.validate_config(config_no_good)
# print(res)

# res = my_mona_client.validate_config(config)
# print(res)

# print("---------Tests: get_config_history- good-------------------------------------")
# res = my_mona_client.get_config_history()
# print(res)

# print("---------Tests: get_config_history- not good-------------------------------------")
# res = my_mona_client2.get_config_history()
# print(res)

# print("---------Tests: create_sampling_factor-not good------------------------------")
# res = my_mona_client.create_sampling_factor(
#     config_name="smadar@monalabs.io", sampling_factor=2, context_class=context_class_name
# )
# print(res)

# print("---------Tests: create_sampling_factor-good------------------------------")
# res = my_mona_client.create_sampling_factor(
#     config_name="smadar_neti_tests", sampling_factor=1, context_class="nwzz_!"
# )
# print(res)

# print("---------Tests: get_ingested_data_for_a_specific_segment good----------------")
res = my_mona_client.get_suggested_config_from_user_input(
    events={
        "messages": [
            {
                "arcClass": "YOUR_CONTEXT_CLASS",
                "contextId": "someContextId",
                "exportTimestamp": 1644466612,
                "message": {
                    "occupation": "manufacturing",
                    "city": "Fort Smith",
                    "state": "Arkansas",
                    "purpose": "Credit score improvement",
                    "credit_score": 0.3926368592424558,
                    "loan_taken": True,
                    "return_until": 1619948737000,
                    "offered_amount": 2015,
                    "approved_amount": 2015,
                    "stage": "inference",
                    "model_version": "v1",
                },
            },
            {
                "arcClass": "YOUR_CONTEXT_CLASS",
                "contextId": "someContextId",
                "exportTimestamp": 1644488612,
                "message": {
                    "feature_0": 2858561.5949184396,
                    "feature_1": 5.777438394215511,
                    "feature_2": 762,
                    "feature_3": 8102,
                    "feature_4": 0,
                    "feature_5": 0.9689581447209208,
                    "feature_6": 27,
                    "feature_7": 0,
                    "feature_8": 1384.99655593255,
                    "feature_9": 18.11042489302702,
                },
            },
        ]
    }
)
# print(res)

# print("---------Tests: get_ingested_data_for_a_specific_segment not good----------------")
# res = my_mona_client.get_ingested_data_for_a_specific_segment(
#     context_class= context_class_name,
#     start_time =1671551414,
#     end_time=1771551414,
#     segment="AverageDrift"
#
# )
# print(res)

# res = my_mona_client.get_ingested_data_for_a_specific_segment(
#     context_class= context_class_name,
#     start_time =0,
#     end_time=1,
#     segment ={}
# )
# print(res)


# print("---------Tests: get_aggregated_stats_of_a_specific_segmentation not good----------------")
# res = my_mona_client.get_aggregated_stats_of_a_specific_segmentation(
#         context_class= context_class_name,
#         dimension=1,
#         target_time_range=4,
#         compared_time_range=10,
#         metric_1_field="average",
#         metric_2_field= "average",
#         metric_1_type ="Average",
#         metric_2_type ="Average",
#         min_segment_size=0,
#         sort_function ="INC",
#
# )
# print(res)

print("---------Tests: get_aggregated_stats_of_a_specific_segmentation good-----------")
res = my_mona_client.get_aggregated_stats_of_a_specific_segmentation(
    context_class="LOAN_APPLICATION_TUTORIAL",
    dimension="purpose",
    target_time_range=[1618876800, 1619481659],
    compared_time_range=[1617667200, 1618876799],
    metric_1_field="credit_score",
    metric_2_field="loan_taken",
    metric_1_type="average",
    metric_2_type="average",
    min_segment_size=0,
    sort_function="SIZE_TOP",
    excluded_segments=[{"occupation": [{"value": "no category"}]}],
    baseline_segment={
        "city": [{"value": "Arkansas_Fort Smith"}],
        "offered_amount": [{"max_value": 2100, "min_value": 1400}],
    },
    target_segments_filter={"stage": [{"value": "inference"}]},
    compared_segments_filter={"stage": [{"value": "train"}]},
)
# print(res)

# print("---------Tests: get_insights- good-------------------------------------------")
# res = my_mona_client.get_insights(
#     context_class="context_class", min_segment_size=0
# )
# print(res)


# res =my_mona_client.get_insights(
#     context_class="LOAN_APPLICATION_TUTORIAL",
#     min_segment_size=10,
#     time_range_seconds=[0, 1671970079],
# )
# print(res)

# print("---------Tests: get_insights- not good-------------------------------------------")
# res = my_mona_client.get_insights(
#     context_class="c", min_segment_size=0
# )
# print(res)


# print("all done ... ")
