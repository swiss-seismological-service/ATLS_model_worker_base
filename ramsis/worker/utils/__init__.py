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
        return pkg_resources.get_distribution("ramsis.worker").version

# get_version ()

def escape_newline(s):
    """
    Escape newline characters.

    :param str s: String to be processed.
    """
    return s.replace('\n','\\n').replace('\r','\\r')

# ---- END OF <__init__.py> ----
