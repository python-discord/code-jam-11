"""Logging configuration for the project.

Note:
    Whenever logging is needed, the `get_logger` function from this module should be used.
    Do not use the default `logging.getLogger` function, as it does not return the correct logger type.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Any, TYPE_CHECKING, cast

import coloredlogs

from src.utils.config import get_config

# We set these values here instead of getting them from
DEBUG = get_config("DEBUG", cast=bool, default=False)
LOG_FILE = get_config("LOG_FILE", cast=Path, default=None)
TRACE_LEVEL_FILTER = get_config("TRACE_LEVEL_FILTER", default=None)

LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)7s | %(message)s"
TRACE_LEVEL = 5


if TYPE_CHECKING:
    LoggerClass = logging.Logger
else:
    LoggerClass = logging.getLoggerClass()


class CustomLogger(LoggerClass):
    """Custom implementation of the `Logger` class with an added `trace` method."""

    def trace(self, msg: str, *args: object, **kwargs: Any) -> None:
        """Log 'msg % args' with severity 'TRACE'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.trace("Houston, we have an %s", "interesting problem", exc_info=1)
        """
        if self.isEnabledFor(TRACE_LEVEL):
            self.log(TRACE_LEVEL, msg, *args, **kwargs)


def get_logger(name: str | None = None, *, skip_class_check: bool = False) -> CustomLogger:
    """Utility to make the type checker recognise that logger is of type `CustomLogger`.

    Additionally, in case logging isn't already set up, :meth:`.setup_logging` is ran.

    This is necessary as this function is lying to the type-checker by using explicit
    :meth:`cast`, specifying that the logger is of the :class:`CustomLogger` type,
    when in fact it might not be.

    :param skip_class_check:
        When ``True``, the logger class check, which ensures logging was already set up
        will be skipped.

        Do know that disabling this check can be dangerous, as it might result in this
        function returning a regular logger, with typing information of custom logger,
        leading to issues like ``get_logger().trace`` producing an :exc:`AttributeError`.
    """
    if not skip_class_check and logging.getLoggerClass() is not CustomLogger:
        setup_logging()

        # Ideally, we would log this before running the setup_logging function, however
        # we that would produce an unformatted (default) log, which is not what we want.
        log = logging.getLogger(__name__)
        log.debug("Ran setup_log (logger was requested).")

    return cast(CustomLogger, logging.getLogger(name))


def setup_logging() -> None:
    """Sets up logging library to use our logging configuration.

    This function only needs to be called once, at the program start.
    """
    # This indicates that logging was already set up, no need to do it again
    if logging.getLoggerClass() is CustomLogger:
        log = get_logger(__name__)
        log.debug("Attempted to setup logging, when it was already set up")
        return

    # Setup log levels first, so that get_logger will not attempt to call setup_logging itself.
    _setup_trace_level()

    root_log = get_logger()
    _setup_coloredlogs(root_log)
    _setup_logfile(root_log)
    _setup_log_levels(root_log)
    _setup_external_log_levels(root_log)


def _setup_trace_level() -> None:
    """Setup logging to recognize our new TRACE level."""
    logging.TRACE = TRACE_LEVEL  # pyright: ignore[reportAttributeAccessIssue]
    logging.addLevelName(TRACE_LEVEL, "TRACE")
    logging.setLoggerClass(CustomLogger)


def _setup_coloredlogs(root_log: LoggerClass) -> None:
    """Install coloredlogs and set it up to use our log format."""
    if "COLOREDLOGS_LOG_FORMAT" not in os.environ:
        coloredlogs.DEFAULT_LOG_FORMAT = LOG_FORMAT

    if "COLOREDLOGS_LEVEL_STYLES" not in os.environ:
        coloredlogs.DEFAULT_LEVEL_STYLES = {
            **coloredlogs.DEFAULT_LEVEL_STYLES,
            "trace": {"color": 246},
            "critical": {"background": "red"},
        }

    if "COLOREDLOGS_DEFAULT_FIELD_STYLES" not in os.environ:
        coloredlogs.DEFAULT_FIELD_STYLES = {
            **coloredlogs.DEFAULT_FIELD_STYLES,
            "levelname": {"color": "magenta", "bold": True},
        }

    # The log level here is set to TRACE, so that coloredlogs covers all messages.
    # This however doesn't mean that our log level will actually be set to TRACE,
    # that's configured by setting the root log's log level directly.
    coloredlogs.install(level=TRACE_LEVEL, logger=root_log, stream=sys.stdout)


def _setup_logfile(root_log: LoggerClass) -> None:
    """Setup a file handle for logging using our log format."""
    if LOG_FILE is None:
        return

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(LOG_FILE)
    log_formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(log_formatter)
    root_log.addHandler(file_handler)


def _setup_log_levels(root_log: LoggerClass) -> None:
    """Set loggers to the log levels according to the value from the TRACE_LEVEL_FILTER and DEBUG env vars.

    DEBUG env var:
        - When set to a truthy value (1,true,yes), the root log level will be set to DEBUG.
        - Otherwise (including if not set at all), the root log level will be set to INFO.

    TRACE_LEVEL_FILTER env var:
        This variable is ignored if DEBUG is not set to a truthy value!

        - If not set, no trace logs will appear and root log will be set to DEBUG.
        - If set to "*", the root logger will be set to the TRACE level. All trace logs will appear.
        - When set to a list of logger names, delimited by a comma, each of the listed loggers will
          be set to the TRACE level. The root logger will retain the DEBUG log level.
        - If this list is prefixed by a "!", the root logger is set to TRACE level, with all of the
          listed loggers set to a DEBUG log level.
    """
    # DEBUG wasn't specified, no DEBUG level logs (INFO log level)
    if not DEBUG:
        root_log.setLevel(logging.INFO)
        return

    # TRACE_LEVEL_FILTER wasn't specified, no TRACE level logs (DEBUG log level)
    if TRACE_LEVEL_FILTER is None:
        root_log.setLevel(logging.DEBUG)
        return

    # TRACE_LEVEL_FILTER enables all TRACE loggers
    if TRACE_LEVEL_FILTER == "*":
        root_log.setLevel(TRACE_LEVEL)
        return

    # TRACE_LEVEL_FILTER is a list of loggers to not set to TRACE level (default is TRACE)
    if TRACE_LEVEL_FILTER.startswith("!"):
        root_log.setLevel(TRACE_LEVEL)
        for logger_name in TRACE_LEVEL_FILTER.removeprefix("!").strip(",").split(","):
            get_logger(logger_name).setLevel(logging.DEBUG)
        return

    # TRACE_LEVEL_FILTER is a list of loggers to set to TRACE level
    root_log.setLevel(logging.DEBUG)
    for logger_name in TRACE_LEVEL_FILTER.strip(",").split(","):
        get_logger(logger_name).setLevel(TRACE_LEVEL)


def _setup_external_log_levels(root_log: LoggerClass) -> None:
    """Set log levels of some external libraries explicitly.

    Some libraries produce a lot of logs which we don't necessarily need to see,
    and they often tend to clutter our own. These libraries have their log levels
    set explicitly here, avoiding unneeded spammy logs.
    """
    get_logger("asyncio").setLevel(logging.INFO)
    get_logger("aiosqlite").setLevel(logging.INFO)
    get_logger("alembic.runtime.migration").setLevel(logging.WARNING)

    get_logger("parso").setLevel(logging.WARNING)  # For usage in IPython
