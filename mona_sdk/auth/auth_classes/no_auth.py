from mona_sdk.auth.auth_classes.base_auth import Base
from mona_sdk.messages import UNAUTHENTICATED_CHECK_ERROR_MESSAGE


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

    @staticmethod
    def get_unauthenticated_mode_error_message():
        return UNAUTHENTICATED_CHECK_ERROR_MESSAGE

    def is_authentication_used(self):
        return False


