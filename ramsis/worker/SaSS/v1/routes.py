# This is <routes.py>
# -----------------------------------------------------------------------------
#
# Purpose: SaSS worker routes.
#
# Copyright (c) Daniel Armbruster (SED, ETH), Lukas Heiniger (SED, ETH)
#
# REVISION AND CHANGES
# 2018/08/10        V0.1    Daniel Armbruster
# =============================================================================
"""
SaSS resource facilities.
"""

from flask_restful import Api

from ramsis.worker.SaSS import db, settings
from ramsis.worker.SaSS.model import Model
from ramsis.worker.SaSS.v1 import blueprint
from ramsis.worker.SaSS.v1.schema import SFMWorkerInputMessageSchema
from ramsis.worker.utils.parser import parser
from ramsis.worker.utils.resource import (SFMRamsisWorkerResource,
                                          SFMRamsisWorkerListResource)


api_v1 = Api(blueprint)


class SaSSAPI(SFMRamsisWorkerResource):

    LOGGER = 'ramsis.worker.sass_resource'

# class SaSSAPI

class SaSSListAPI(SFMRamsisWorkerListResource):
    """
    Concrete implementation of an asynchronous SaSS worker resource.

    :param model: Model to be handled by :py:class:`SaSSListAPI`.
    :type model: :py:class:`ramsis.worker.SaSS.model.SaSSModel`
    """
    LOGGER = 'ramsis.worker.sass_list_resource'

    def _parse(self, request, locations=('json', )):
        return parser.parse(SFMWorkerInputMessageSchema(), request,
                            locations=locations)

# class SaSSListResource


api_v1.add_resource(SaSSAPI,
                    '{}/<task_id>'.format(settings.PATH_RAMSIS_SASS_SCENARIOS),
                    resource_class_kwargs={
                        'db': db})

api_v1.add_resource(SaSSListAPI,
                    settings.PATH_RAMSIS_SASS_SCENARIOS,
                    resource_class_kwargs={
                        'model': Model,
                        'db': db})

# ---- END OF <routes.py> ----
