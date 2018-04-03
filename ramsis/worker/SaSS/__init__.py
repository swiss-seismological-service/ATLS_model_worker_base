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

from flask import Flask

__version__ = '0.1'


def create_app(config_dict={}):
    """
    Factory function for Flask application.

    :param :cls:`flask.Config config` flask configuration object
    """
    app = Flask(__name__)

    return app

# create_app ()

# ---- END OF <__init__.py> ----
