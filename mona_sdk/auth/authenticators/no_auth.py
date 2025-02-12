from mona_sdk.messages import UNAUTHENTICATED_CHECK_ERROR_MESSAGE
from mona_sdk.auth.authenticators.base_authenticator import BaseAuthenticator


class NoAuth(BaseAuthenticator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def initial_auth(self):
        return True

    def is_authenticated(self):
        return True

    def request_access_token(self):
        raise NotImplementedError

    def request_refresh_token(self):
        raise NotImplementedError

    def should_refresh_token(self):
        return False

    @staticmethod
    def get_unauthenticated_mode_error_message():
        return UNAUTHENTICATED_CHECK_ERROR_MESSAGE

    def is_authentication_used(self):
        return False
