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

import os
import functools

from flask_restful import Api

from ramsis.worker import settings
from ramsis.worker.SaSS import db
from ramsis.worker.SaSS.model import Model
from ramsis.worker.SaSS.v1 import blueprint
from ramsis.worker.SaSS.v1.schema import WorkerInputMessageSchema
from ramsis.worker.utils.parser import parser
from ramsis.worker.utils.resource import (RamsisWorkerResource,
                                          RamsisWorkerListResource)


api_v1 = Api(blueprint)


class SaSSAPI(RamsisWorkerResource):

    LOGGER = 'ramsis.worker.sass_resource'

# class SaSSAPI

class SaSSListAPI(RamsisWorkerListResource):
    """
    Concrete implementation of an asynchronous SaSS worker resource.

    :param model: Model to be handled by :py:class:`SaSSListAPI`.
    :type model: :py:class:`ramsis.worker.SaSS.model.SaSSModel`
    """
    LOGGER = 'ramsis.worker.sass_list_resource'

    def _parse(self, request, locations=('json', )):
        return parser.parse(WorkerInputMessageSchema(), request,
                            locations=locations)

# class SaSSListResource


api_v1.add_resource(SaSSAPI,
                    '{}/<task_id>'.format(settings.PATH_RAMSIS_SASS_SCENARIOS),
                    resource_class_kwargs={
                        'db': db})

# XXX(damb): Bind parameters to the SaSSModel's constructor.
Model.__init__ = functools.partialmethod(
    Model.__init__,
    matlab_opts='-sd {}'.format(
        os.path.join(os.path.dirname(os.path.realpath(__file__)),
                     os.pardir,
                     'model')))

api_v1.add_resource(SaSSListAPI,
                    settings.PATH_RAMSIS_SASS_SCENARIOS,
                    resource_class_kwargs={
                        'model': Model,
                        'db': db})

# ---- END OF <routes.py> ----
