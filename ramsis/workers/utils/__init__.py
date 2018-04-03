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
General purpose ramsis.workers utilities
"""

import argparse
import os
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
        return pkg_resources.get_distribution("ramsis.workers").version

# get_version ()

def realpath(p):
    return os.path.realpath(os.path.expanduser(p))

# realpath ()

def real_file_path(path):
    """
    check if file exists
    :returns: realpath in case the file exists
    :rtype: str
    :raises argparse.ArgumentTypeError: if file does not exist
    """
    path = realpath(path)
    if not os.path.isfile(path):
        raise argparse.ArgumentTypeError(
            '{0!r} is not a valid file path.'.format(path))
    return path

# real_file_path ()


# ---- END OF <__init__.py> ----
