import asyncio
from functools import wraps, partial
from mona_sdk import Client

"""
Implementation based on: 
https://stackoverflow.com/questions/51649227/wrap-all-class-methods-using-a-meta-class
"""


def async_wrap(client_event_loop=None, client_executor=None):
    def run_outer(func):
        @wraps(func)
        async def run_inner(
            *args, event_loop=client_event_loop, executor=client_executor, **kwargs
        ):
            if event_loop is None:
                event_loop = asyncio.get_event_loop()
            pfunc = partial(func, *args, **kwargs)
            return await event_loop.run_in_executor(executor, pfunc)

        return run_inner

    return run_outer


# def async_wrap(func):
#    @wraps(func)
#    async def run(*args, loop=None, executor=None, **kwargs):
#        print("hey func is wrapped")
#        if loop is None:
#            loop = asyncio.get_event_loop()
#        pfunc = partial(func, *args, **kwargs)
#        return await loop.run_in_executor(executor, pfunc)
#
#    return run


class AsyncMeta(type):
    def __init__(self, class_name, bases, class_dict):
        print("meta.__init__()")
        print(dir(self))
        # event_loop = getattr(self, "event_loop") if "event_loop" in dir(self) else None
        # executor = getattr(self, "executor") if "executor" in dir(self) else None

        for attr_name in dir(self):
            if attr_name.startswith("__"):  # == "__class__" or attr_name == "__init__":
                # the metaclass is a callable attribute too,
                # but we want to leave this one alone
                continue

            current_method = getattr(self, attr_name)
            if hasattr(current_method, "__call__"):
                current_method_as_asynch = async_wrap(current_method)
                setattr(self, f"{attr_name}_asynch", current_method_as_asynch)
        print(dir(self))
        # not need for the `return` here
        super(AsyncMeta, self).__init__(class_name, bases, class_dict)


class AsyncClient(Client, metaclass=AsyncMeta):
    def __init__(self, *args, **kwargs):
        print("child.__init__()")
        super().__init__(*args, **kwargs)


