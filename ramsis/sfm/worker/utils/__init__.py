# This is <__init__.py>
# -----------------------------------------------------------------------------
#
# Purpose: General purpose utilities.
#
# Copyright (c) Daniel Armbruster (SED, ETH), Lukas Heiniger (SED, ETH)
#
# REVISION AND CHANGES
# 2018/04/03        V0.1    Daniel Armbruster
# =============================================================================
"""
General purpose ramsis.sfm.workers utilities
"""
import argparse
import logging
import pkg_resources


# -----------------------------------------------------------------------------
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

# get_version ()

def escape_newline(s):
    """
    Escape newline characters.

    :param str s: String to be processed.
    """
    return s.replace('\n', '\\n').replace('\r', '\\r')

# escape_newline ()

def url(url):
    """
    check if SQLite URL is absolute.
    """
    if (url.startswith('sqlite:') and not
            (url.startswith('////', 7) or url.startswith('///C:', 7))):
        raise argparse.ArgumentTypeError('SQLite URL must be absolute.')
    return url

# url ()


class ContextLoggerAdapter(logging.LoggerAdapter):
    """
    Adapter expecting the passed in dict-like object to have a 'ctx' key, whose
    value in brackets is prepended to the log message.
    """
    def process(self, msg, kwargs):
        return '[%s] %s' % (self.extra['ctx'], msg), kwargs


# ---- END OF <__init__.py> ----
