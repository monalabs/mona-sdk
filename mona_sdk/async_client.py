import asyncio
from typing import List
from functools import wraps, partial

from mona_sdk import Client
from mona_sdk.client import UNPROVIDED_VALUE, MonaSingleMessage


def async_wrap(func):
    """
    Wraps the synchronous methods to asynchronous methods using run_in_executor that
    open a new thread to run the method in.
    This implementation is based on the second answer here:
    https://stackoverflow.com/questions/43241221/how-can-i-wrap-a-synchronous-function-in-an-async-coroutine
    """

    @wraps(func)
    async def run_inner(*args, **kwargs):
        async_client = args[0]
        final_event_loop = (
            kwargs.pop("event_loop", None)
            or async_client._event_loop
            or asyncio.get_event_loop()
        )
        final_executor = kwargs.pop("executor", None) or async_client._executor
        partial_function = partial(func, *args, **kwargs)
        return await final_event_loop.run_in_executor(final_executor, partial_function)

    return run_inner


class AsyncMeta(type):
    def __init__(metacls, class_name, bases, class_dict):
        for attr_name in dir(metacls):
            if (
                attr_name.startswith("__")
                or attr_name.startswith("_")
                or attr_name.endswith("_async")
            ):
                continue

            current_method = getattr(metacls, attr_name)
            if hasattr(current_method, "__call__"):
                current_method_as_async = async_wrap(current_method)
                setattr(metacls, f"{attr_name}_async", current_method_as_async)
        # no need for `return` here
        super(AsyncMeta, metacls).__init__(class_name, bases, class_dict)


class AsyncClient(Client, metaclass=AsyncMeta):
    """
    This client wraps each of the methods in the regular synchronous client using
    run_in_executor. This way, the method becomes non-blocking. The asynchronous methods
    are stored as new methods with 'async' suffix (for example, the async version of
    export_batch is async version is export_batch_async).
    """

    def __init__(self, *args, event_loop=None, executor=None, **kwargs):
        """
        Creates the AsyncClient object.
        :param event_loop: optional.
        :param executor: optional.
        """
        super().__init__(*args, **kwargs)
        self._event_loop = event_loop
        self._executor = executor

    # We add the signatures of the public methods of the synchronous client because the
    # IDE raises warning for methods that doesn't appear explicitly in the class.
    def export_async(
        self,
        message: MonaSingleMessage,
        filter_none_fields=None,
        event_loop=None,
        executor=None,
    ):
        pass

    def export_batch_async(
        self,
        events: List[MonaSingleMessage],
        default_action=None,
        filter_none_fields=None,
        event_loop=None,
        executor=None,
    ):
        pass

    def is_active_async(
        self,
        event_loop=None,
        executor=None,
    ):
        pass

    def upload_config_async(
        self, config, commit_message, author=None, event_loop=None, executor=None
    ):
        pass

    def upload_config_per_context_class_async(
        self,
        author,
        commit_message,
        context_class,
        config,
        event_loop=None,
        executor=None,
    ):
        pass

    def get_config_async(self, event_loop=None, executor=None):
        pass

    def get_suggested_config_async(self, event_loop=None, executor=None):
        pass

    def get_config_history_async(
        self, number_of_revisions=UNPROVIDED_VALUE, event_loop=None, executor=None
    ):
        pass

    def get_sampling_factors_async(self, event_loop=None, executor=None):
        pass

    def create_sampling_factor_async(
        self,
        config_name,
        sampling_factor,
        context_class=None,
        event_loop=None,
        executor=None,
    ):
        pass

    def validate_config_async(
        self,
        config,
        list_of_context_ids=UNPROVIDED_VALUE,
        latest_amount=UNPROVIDED_VALUE,
        event_loop=None,
        executor=None,
    ):
        pass

    def validate_config_per_context_class_async(
        self,
        config,
        context_class,
        list_of_context_ids=UNPROVIDED_VALUE,
        latest_amount=UNPROVIDED_VALUE,
    ):
        pass

    def get_insights_async(
        self,
        context_class,
        min_segment_size,
        insight_types=UNPROVIDED_VALUE,
        metric_name=UNPROVIDED_VALUE,
        min_insight_score=UNPROVIDED_VALUE,
        time_range_seconds=UNPROVIDED_VALUE,
        first_discovered_on_range_seconds=UNPROVIDED_VALUE,
        event_loop=None,
        executor=None,
    ):
        pass

    def get_ingested_data_for_a_specific_segment_async(
        self,
        context_class,
        start_time,
        end_time,
        segment,
        sampling_threshold=UNPROVIDED_VALUE,
        excluded_segments=UNPROVIDED_VALUE,
        event_loop=None,
        executor=None,
    ):
        pass

    def get_suggested_config_from_user_input_async(
        self, events, event_loop=None, executor=None
    ):
        pass

    def get_aggregated_data_of_a_specific_segment_async(
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
        event_loop=None,
        executor=None,
    ):
        pass

    def get_aggregated_stats_of_a_specific_segmentation_async(
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
        event_loop=None,
        executor=None,
    ):
        pass
