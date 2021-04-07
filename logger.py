"""
Module providing MONA logger configurations.
"""
import os
import logging
from threading import Lock

LOGGER_NAME = os.environ.get("MONA_LOGGER_NAME", "mona-logger")

# Possible logging level string values: CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET.
# When MONA_LOGGING_LEVEL is not provided (or holds an unknown value), logger will be
# off.
LOGGING_LEVEL = os.environ.get("MONA_LOGGING_LEVEL")

logger = None
logger_lock = Lock()


def get_logger():
    global logger
    if not logger:
        with logger_lock:
            # The inner check is needed to avoid multiple create_new_logger() calls.
            if not logger:
                _create_new_logger()
    return logger


def _create_new_logger():
    global logger
    logger = logging.getLogger(LOGGER_NAME)

    if LOGGING_LEVEL:
        if LOGGING_LEVEL.isnumeric():
            logger.setLevel(int(LOGGING_LEVEL))
        else:
            try:
                logger.setLevel(LOGGING_LEVEL)
            except ValueError:
                logger.error(
                    "Tried to set mona logging level to an unknown level, turning logs"
                    "off."
                )
                logger.setLevel(logging.CRITICAL + 1)
    else:
        # LOGGING_LEVEL was not provided, turning logs off.
        # (Setting level to CRITICAL + 1 as seen here:
        #   https://stackoverflow.com/a/61333099)
        logger.setLevel(logging.CRITICAL + 1)
