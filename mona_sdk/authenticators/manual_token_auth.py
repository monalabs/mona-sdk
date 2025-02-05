from mona_sdk.auth import API_KEYS_TO_TOKEN_DATA
from mona_sdk.auth_globals import MANUAL_TOKEN_STRING_FOR_API_KEY, IS_AUTHENTICATED
from mona_sdk.authenticators.base_auth import Base
from mona_sdk.logger import get_logger


# todo make sure I rename it here
class ManualTokenAuth(Base):
    def __init__(self, access_token, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def initial_auth(self):
        get_logger().info("Manual token mode is on.")

        # todo this is going to change here.
        API_KEYS_TO_TOKEN_DATA[MANUAL_TOKEN_STRING_FOR_API_KEY] = {
            # todo where is this going to come from?
            #   let's assume that
            # todo it's interesting - wri
            # ACCESS_TOKEN: mona_client.get_manual_access_token(),
            IS_AUTHENTICATED: True,
        }

        return True

    def is_authenticated(self, _):
        return True

    def should_refresh_token(_):
        return False

