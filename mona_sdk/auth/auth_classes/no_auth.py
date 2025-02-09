from mona_sdk.auth.auth_classes.base_auth import Base


class NoAuth(Base):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _raise_if_missing_params(self):
        pass

    def initial_auth(self):
        return True

    def is_authenticated(self):
        return True

    def should_refresh_token(self):
        return False
