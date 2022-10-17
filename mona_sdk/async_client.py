import asyncio
from functools import wraps, partial
from mona_sdk import Client


def async_wrap(func):
    """
    Wraps the synchronous methods to asynchronous methods.
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
        return await final_event_loop.run_in_executor(
            final_executor, partial_function
        )
    return run_inner


class AsyncMeta(type):
    def __init__(
        metacls, class_name, bases, class_dict
    ):
        for attr_name in dir(metacls):
            if attr_name.startswith("__") or attr_name.startswith("_"):
                continue

            current_method = getattr(metacls, attr_name)
            if hasattr(current_method, "__call__"):
                current_method_as_async = async_wrap(
                    current_method
                )
                setattr(metacls, f"{attr_name}_async", current_method_as_async)
        # not need for the `return` here
        super(AsyncMeta, metacls).__init__(class_name, bases, class_dict)


class AsyncClient(
    Client, metaclass=AsyncMeta
):
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
