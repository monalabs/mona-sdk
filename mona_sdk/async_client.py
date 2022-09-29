import asyncio
from functools import wraps, partial
from mona_sdk import Client

"""
Implementation based on: 
https://stackoverflow.com/questions/51649227/wrap-all-class-methods-using-a-meta-class
"""


def async_wrap(func):
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
    def __init__(self, *args, event_loop=None, executor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._event_loop = event_loop
        self._executor = executor
