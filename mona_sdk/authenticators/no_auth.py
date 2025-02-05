from mona_sdk.authenticators.base_auth import Base


class NoAuth(Base):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def initial_auth(self):
        return True

    # todo let's think about what this whole thing does
    #   when we're calling


    # todo can we be static everywhere?
    @staticmethod
    def is_authenticated(_):
        return True

    @staticmethod
    def should_refresh_token():
        return False
