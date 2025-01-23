from functools import wraps

from auth import (
    is_authenticated,
    _handle_authentications_error,
    _should_refresh_token,
    authentication_lock,
    _refresh_token,
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
            # args[0] is the current mona_client instance.
            mona_client = args[0]

            if not mona_client.should_use_authentication:
                return decorated(*args, **kwargs)

            # If len(args) < 1, the wrapped function does not have args to log (neither
            # messages nor config)
            should_log_args = len(args) > 1 and mona_client.should_log_failed_messages

            # message_to_log is the messages/config that should be logged in case of
            # an authentication failure.
            message_to_log = args[1] if should_log_args else None

            # todo where is the key coming from?
            if not is_authenticated(mona_client.api_key):
                return _handle_authentications_error(
                    "Mona's client is not authenticated",
                    mona_client.raise_authentication_exceptions,
                    message_to_log,
                )

            if _should_refresh_token(mona_client):
                with authentication_lock:
                    # The inner check is needed to avoid double token refresh.
                    if _should_refresh_token(mona_client):
                        refresh_token_response = _refresh_token(mona_client)

                        if not refresh_token_response.ok:
                            # TODO(anat): Check if the current token is still valid to
                            #   call the function anyway.
                            return _handle_authentications_error(
                                f"Could not refresh token: "
                                f"{refresh_token_response.text}",
                                mona_client.raise_authentication_exceptions,
                                message_to_log,
                            )

            # todo I'm not sure here where exactly are we going here
            return decorated(*args, **kwargs)

        return inner
