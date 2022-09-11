from functools import wraps

from mona_sdk.authentication import (
    is_authenticated,
    handle_authentications_error,
    should_refresh_token,
    authentication_lock,
    refresh_token,
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

            if not is_authenticated(mona_client.api_key):
                return handle_authentications_error(
                    "Mona's client is not authenticated",
                    mona_client.raise_authentication_exceptions,
                    message_to_log,
                )

            if should_refresh_token(mona_client.api_key):
                with authentication_lock:
                    # The inner check is needed to avoid double token refresh.
                    if should_refresh_token(mona_client.api_key):
                        refresh_token_response = refresh_token(mona_client)
                        if not refresh_token_response.ok:
                            # TODO(anat): Check if the current token is still valid to
                            #   call the function anyway.
                            return handle_authentications_error(
                                f"Could not refresh token: "
                                f"{refresh_token_response.text}",
                                mona_client.raise_authentication_exceptions,
                                message_to_log,
                            )
            return decorated(*args, **kwargs)

        return inner

    @classmethod
    def update_sampling_factors_if_needed(cls, decorated):
        """
        This decorator checks if the current client's sampling factors configuration
        has been changed, and if so, updates the client to use its new values.
        """

        @wraps(decorated)
        def inner(*args, **kwargs):
            # args[0] is the current mona_client instance.
            mona_client = args[0]

            if mona_client.sampling_config_name:
                # Get the updated config from the index.
                sampling_config = mona_client.get_sampling_factors()[0]

                default_from_index = sampling_config.get("default_factor")
                factors_map_from_index = sampling_config.get("factors_map")

                # If the factors map or the default was changed, update the client
                # accordingly.

                if (
                    default_from_index is not None
                    and default_from_index != mona_client.default_sampling_rate
                ):
                    mona_client.default_sampling_rate = default_from_index

                if (
                    factors_map_from_index
                    and factors_map_from_index
                    != mona_client.context_class_to_sampling_rate
                ):
                    mona_client.context_class_to_sampling_rate = factors_map_from_index

            return decorated(*args, **kwargs)

        return inner