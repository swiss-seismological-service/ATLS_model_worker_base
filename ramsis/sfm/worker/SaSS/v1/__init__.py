# This is <__init__.py>
# -----------------------------------------------------------------------------
#
# Purpose: SaSS worker v1 blueprint.
#
# Copyright (c) Daniel Armbruster (SED, ETH), Lukas Heiniger (SED, ETH)
#
# REVISION AND CHANGES
# 2018/08/10        V0.1    Daniel Armbruster
# =============================================================================
from flask import Blueprint

API_VERSION_V1 = 1
API_VERSION = API_VERSION_V1

blueprint = Blueprint('v1', __name__)

# XXX(damb): Register modules with blueprint.
from ramsis.sfm.worker.SaSS.v1 import routes, schema

# ---- END OF <__init__.py> ----
