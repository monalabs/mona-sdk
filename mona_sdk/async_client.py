import asyncio
from functools import wraps, partial
from mona_sdk import Client

"""
Implementation based on: 
https://stackoverflow.com/questions/51649227/wrap-all-class-methods-using-a-meta-class
"""


def async_wrap(func, client_event_loop=None, client_executor=None):
    event_loop = (
        asyncio.get_event_loop() if not client_event_loop else client_event_loop
    )

    def run_outer():
        @wraps(func)
        async def run_inner(*args, **kwargs):
            pfunc = partial(func, *args, **kwargs)
            return await event_loop.run_in_executor(client_executor, pfunc)

        return run_inner

    return run_outer()


class AsyncMeta(type):
    def __new__(metacls, name, bases, namespace, **kwargs):
        # kwargs = {"loop": 1, "executor": 2}
        return super().__new__(metacls, name, bases, namespace)

    def __init__(metacls, class_name, bases, class_dict, **kwargs):
        event_loop = kwargs["client_loop"] if "client_loop" in kwargs else None
        executor = kwargs["client_executor"] if "client_executor" in kwargs else None
        print("meta.__init__()")
        print(dir(metacls))

        for attr_name in dir(metacls):
            if attr_name.startswith("__") or attr_name.startswith("_"):
                continue

            current_method = getattr(metacls, attr_name)
            if hasattr(current_method, "__call__"):
                current_method_as_asynch = async_wrap(
                    current_method,
                    client_event_loop=event_loop,
                    client_executor=executor,
                )
                setattr(metacls, f"{attr_name}_asynch", current_method_as_asynch)
        print(dir(metacls))
        # not need for the `return` here
        super(AsyncMeta, metacls).__init__(class_name, bases, class_dict)


def get_async_client(*args, event_loop=None, executor=None, **kwargs):
    class AsyncClient(
        Client, metaclass=AsyncMeta, client_loop=event_loop, client_executor=executor
    ):
        def __init__(self, args, kwargs):
            print("child.__init__()")
            super().__init__(*args, **kwargs)

    return AsyncClient(args, kwargs)
