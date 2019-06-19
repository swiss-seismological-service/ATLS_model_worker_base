# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
General purpose ramsis.sfm.workers utilities
"""
import argparse
import enum
import logging
import pkg_resources


def get_version(namespace_pkg_name=None):
    """
    fetch version string

    :param str namespace_pkg_name: distribution name of the namespace package
    :returns: version string
    :rtype: str
    """
    try:
        # distributed as namespace package
        if namespace_pkg_name:
            return pkg_resources.get_distribution(namespace_pkg_name).version
        raise
    except Exception:
        return pkg_resources.get_distribution("ramsis.sfm.worker").version


def escape_newline(s):
    """
    Escape newline characters.

    :param str s: String to be processed.
    """
    return s.replace('\n', '\\n').replace('\r', '\\r')


def url(url):
    """
    check if SQLite URL is absolute.
    """
    if (url.startswith('sqlite:') and not
            (url.startswith('////', 7) or url.startswith('///C:', 7))):
        raise argparse.ArgumentTypeError('SQLite URL must be absolute.')
    return url


class ContextLoggerAdapter(logging.LoggerAdapter):
    """
    Adapter expecting the passed in dict-like object to have a 'ctx' key, whose
    value in brackets is prepended to the log message.
    """
    def process(self, msg, kwargs):
        return '[%s] %s' % (self.extra['ctx'], msg), kwargs


class StatusCode(enum.Enum):
    """
    SFM-Worker status code enum.
    """
    # codes related to worker states
    TaskAccepted = 202
    TaskProcessing = 423
    TaskError = 418
    TaskCompleted = 200
    TaskNotAvailable = 204
    # codes related to worker resource
    HTTPMethodNotAllowed = 405
    UnprocessableEntity = 422
    WorkerError = 500
