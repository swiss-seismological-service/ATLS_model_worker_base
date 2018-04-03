# This is <error.py>
# -----------------------------------------------------------------------------
#
# Purpose: error facilities
#
# Copyright (c) Daniel Armbruster (ETH)
#
# REVISION AND CHANGES
# 2018/02/12        V0.1    Daniel Armbruster
# =============================================================================
"""
Error and exception facilities.
"""
import enum


class ExitCode(enum.Enum):
    EXIT_SUCCESS = 0
    EXIT_WARNING = 1
    EXIT_ERROR = 2

# class ExitCode


class Error(Exception):
    """Error base class"""

    # if we raise such an Error and it is only catched by the uppermost
    # exception handler (that exits short after with the given exit_code),
    # it is always a (fatal and abrupt) EXIT_ERROR, never just
    # a warning.
    exit_code = ExitCode.EXIT_ERROR.value
    # show a traceback?
    traceback = False

    def __init__(self, *args):
        super().__init__(*args)
        self.args = args

    def get_message(self):
        return type(self).__doc__.format(*self.args)

    __str__ = get_message

# class Error


class ErrorWithTraceback(Error):
    """Error with traceback."""
    traceback = True


# ---- END OF <error.py> ----
