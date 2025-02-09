from functools import wraps

from mona_sdk.auth.auth_utils import (
    authentication_lock,
    handle_authentications_error,
)


class Decorators(object):
    @classmethod
    def refresh_token_if_needed(cls, decorated):
        """
        This decorator checks if the current client's access token is about to
        be expired/already expired, and if so, updates to a new one.
        """

        @wraps(decorated)
        def inner(*args, **kwargs):
            # Since we are decorating a method, the first argument is self, which is the
            # Mona Client instance.
            mona_client = args[0]

            # If len(args) < 1, the wrapped function does not have args to log (neither
            # messages nor config)
            should_log_args = len(args) > 1 and mona_client.should_log_failed_messages

            # message_to_log is the messages/config that should be logged in case of
            # an authentication failure.
            message_to_log = args[1] if should_log_args else None

            if not mona_client.authenticator.is_authenticated():
                return handle_authentications_error(
                    "Mona's client is not authenticated",
                    mona_client.authenticator.raise_auth_exceptions,
                    message_to_log,
                )

            if mona_client.authenticator.should_refresh_token():
                with authentication_lock:
                    # The inner check is needed to avoid double token refresh.

                    if mona_client.authenticator.should_refresh_token():
                        refresh_token_response = (
                            mona_client.authenticator.refresh_token()
                        )

                        if not refresh_token_response.ok:

                            # TODO(anat): Check if the current token is still valid to
                            #   call the function anyway.
                            return handle_authentications_error(
                                f"Could not refresh token: "
                                f"{refresh_token_response.text}",
                                should_raise_exception=(
                                    mona_client.authenticator.raise_auth_exceptions
                                ),
                                message_to_log=message_to_log,
                            )

            return decorated(*args, **kwargs)

        return inner
