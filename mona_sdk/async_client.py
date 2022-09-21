from mona_sdk import Client


class AsyncClient(Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def wrapper(func):
    def wrapped(self, *args, **kwargs):
        res = func(self, *args, **kwargs)
        return res
    return wrapped


class MyMeta(type):
    def __init__(cls, classname, bases, class_dict):
        for attr_name in dir(cls):
            if attr_name == "__class__":
                # the metaclass is a callable attribute too,
                # but we want to leave this one alone
                continue
            attr = getattr(cls, attr_name)
            if hasattr(attr, '__call__'):
                attr = wrapper(attr)
                setattr(cls, attr_name, attr)

        # not need for the `return` here
        super(MyMeta).__init__(classname, bases, class_dict)


class AsyncClient(metaclass=MyMeta):
    def __init__(self, *args):
        print('child.__init__()')
        super(AsyncClient).__init__(*args)

