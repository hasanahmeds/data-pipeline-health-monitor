"""Logging setup for pipelinescope using py-logex-enhanced"""

import warnings

from py_logex import get_logger as _get_logger

warnings.filterwarnings(action="ignore", category=DeprecationWarning)


_logger = None


def get_logger():
    global _logger

    if _logger is None:
        _logger = _get_logger()

    return _logger


def setup_logging(output_dir=None, log_file=None, enable_console=None, log_level=None):
    get_logger()


def reset_logging():
    global _logger
    _logger = None
