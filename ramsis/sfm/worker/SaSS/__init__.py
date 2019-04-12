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

import uuid

from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy

__version__ = '0.1'

db = SQLAlchemy()

def create_app(config_dict={}):
    """
    Factory function for Flask application.

    :param :cls:`flask.Config config` flask configuration object
    """
    app = Flask(__name__)
    app.config.update(config_dict)

    db.init_app(app)

    # XXX(damb): Avoid circular imports.
    from ramsis.sfm.worker.SaSS.v1 import blueprint as api_v1_bp, API_VERSION_V1
    app.register_blueprint(
        api_v1_bp,
        url_prefix='/v{version}'.format(version=API_VERSION_V1))

    @app.before_request
    def generate_request_id():
        """
        Generate a unique request identifier.
        """
        g.request_id = uuid.uuid4()

    return app

# create_app ()

# ---- END OF <__init__.py> ----
