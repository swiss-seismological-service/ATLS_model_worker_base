# This is <parser.py>
# -----------------------------------------------------------------------------
#
# Purpose: SaSS worker parser facilities.
#
# Copyright (c) Daniel Armbruster (SED, ETH), Lukas Heiniger (SED, ETH)
#
# REVISION AND CHANGES
# 2018/04/16        V0.1    Daniel Armbruster
# =============================================================================
"""
Error handling facilities for worker webservices.
"""


from webargs.flaskparser import abort
from webargs.flaskparser import parser as _parser

from ramsis.utils.protocol import StatusCode


# This error handler is necessary for usage with Flask-RESTful
@_parser.error_handler
def handle_request_parsing_error(err, req, schema):
    """
    Webargs error handler that uses Flask-RESTful's abort function
    to return a JSON error response to the client.
    """
    abort(StatusCode.UnprocessableEntity.value,
          errors=err.messages)

# handle_request_parsing_error ()


parser = _parser

# parser_factory ()

# ---- END OF <parser.py> ----
