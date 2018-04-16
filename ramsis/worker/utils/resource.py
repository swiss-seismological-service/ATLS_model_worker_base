# This is <resource.py>
# -----------------------------------------------------------------------------
#
# Purpose: SaSS worker application facilities.
#
# Copyright (c) Daniel Armbruster (SED, ETH), Lukas Heiniger (SED, ETH)
#
# REVISION AND CHANGES
# 2018/04/10        V0.1    Daniel Armbruster
# =============================================================================
"""
Resource facilities for worker webservices.
"""

import logging

from flask import request
from flask_restful import Resource
from werkzeug.exceptions import HTTPException


from ramsis.utils.error import Error
from ramsis.utils.protocol import StatusCode, WorkerInputMessageSchema
from ramsis.worker.utils import escape_newline
from ramsis.worker.utils.parser import parser
from ramsis.worker.utils.task import TaskError


class WorkerError(Error):
    """Base worker error ({})."""


# TODO(damb):
#   - add output format to protocol
#   - serialize WorkerOutputMessage

# -----------------------------------------------------------------------------
class AbstractWorkerResource(Resource):
    """
    Abstract base class for a worker resource
    """
    LOGGER = 'ramsis.worker_resource'
    TASK = None

    # state storage - this variable is intended to be accessed by means of the
    # corresponding classmethods
    # TODO(damb): Check if the state is handled properly if two workers are
    # running using this base class.
    _STATE = None

    def __init__(self, logger=None):
        self.logger = (logging.getLogger(logger) if logger else
                       logging.getLogger(self.LOGGER))

    # __init__ ()

    @classmethod
    def state(cls):
        return cls._STATE

    @classmethod
    def update_state(cls, val):
        cls._STATE = val

    @classmethod
    def task(cls):
        if cls.TASK is None:
            raise WorkerError('TASK undefined.')
        return cls.TASK

    def get(self):
        return 'Method not allowed.', StatusCode.HTTPMethodNotAllowed.value

    def delete(self):
        return 'Method not allowed.', StatusCode.HTTPMethodNotAllowed.value

    def post(self):
        return 'Method not allowed.', StatusCode.HTTPMethodNotAllowed.value

    def _parse(self, request, locations=('json',)):
        """
        Parse the arguments for a model run. Since `model_parameters` are
        implemented as a simple :cls:`marshmallow.fields.Dict` i.e.

        ..code::

            model_parameters =
            marshmallow.fields.Dict(keys=marshmallow.fields.Str())

        by default no validation is performed on model parameters. However,
        overloading this template function and using a model specific schema
        allows the validation of `model_parameters`.
        """
        return parser.parse(WorkerInputMessageSchema(), request,
                            locations=locations)

# class WorkerResource


class AsyncWorkerResource(AbstractWorkerResource):
    """
    Abstract resource base class for an asyncronous operating worker.
    """
    LOGGER = 'ramsis.worker_resource_async'

    def __init__(self, logger=None):
        logger = logger if logger else self.LOGGER
        super().__init__(logger=logger)

    # __init__ ()

    def get(self):
        """
        HTTP GET method of the async worker webservice API.

        If available returns results else HTTP status code 204.
        """
        if self.state() is None:
            self.logger.debug('No model task currently running.')
            return '', StatusCode.CurrentlyNoTask.value

        return_code = self.state().poll()
        if return_code is None:
            self.logger.debug('Task {0!r} is still running ...'.format(
                self.state()))
            # TODO(damb): Standardize ramsis client return values
            return ({'message': StatusCode.TaskCurrentlyProcessing.name,
                     'result': []}, StatusCode.TaskCurrentlyProcessing.value)

        elif return_code == 0:
            self.logger.debug('Collecting results from task {0!r} ...'.format(
                self.state()))
            if self.state().stdout:
                self.logger.debug(
                    'Task {!r} STDOUT: {}'.format(
                        self.state(),
                        escape_newline(str(self.state().stdout))))
            try:
                # NOTE(damb): Results are assigned during the first GET call
                # after the task finished.
                # TODO(damb): serialize results
                result = self.state().result

            except Exception as err:
                msg = 'Failed to serialize results ({})'.format(err)
                self.logger.warning(msg)
                # TODO(damb): Standardize ramsis client return values
                return ({'message': msg,
                         'result': []}, StatusCode.WorkerError.value)

            # reset and prepare for the next run
            self.state().reset()
            self.update_state(None)

        else:
            self.logger.warning('Task {!r} execution failed.'.format(
                self.state()))
            if self.state().stderr:
                self.logger.debug(
                    'Task {!r} STDERR: {}'.format(
                        self.state(),
                        escape_newline(str(self.state().stderr))))
            self.state().reset()
            self.update_state(None)
            return ({'message': StatusCode.TaskProcessingError.name,
                     'result': []}, StatusCode.TaskProcessingError.value)

        # TODO(damb): Standardize ramsis client return values
        return ({'message': StatusCode.TaskCompleted.name,
                 'result': [{'rate_prediction': result}]},
                StatusCode.TaskCompleted.value)

    # get ()

    def post(self):
        """
        HTTP PUT method of the async worker webservice API.
        """

        self.logger.debug('Received HTTP PUT request ({}).'.format(
                          self.task()))
        if self.state():
            if self.state().poll() is None:
                msg = 'Previous task has not finished yet.'
            elif self.state().poll() == 0 and self.state().result:
                msg = 'Previous results not fetched yet.'

            self.logger.warning(msg)
            # TODO(damb): Standardize ramsis client return values
            return ({'message': msg,
                     'result': []}, StatusCode.PreviousTaskNotCompleted.value)

        try:
            # parse arguments
            args = self._parse(request, locations=('json',))
            self.logger.debug(
                'Configuring task {!r} with parameters {!r} ...'.format(
                    self.task(), args))
            self.task().configure(**args['model_parameters'])
            self.logger.info('Executing task {0!r} ...'.format(self.task()))
            # execute the task
            # XXX(damb): The task itself must be implemented in a way such that
            # it can be executed asynchronously.
            self.task()()
            self.update_state(self.task())

        except TaskError as err:
            self.logger.warning('{}'.format(err))
            self.update_state(None)
            return ({'message': str(err),
                     'result': []}, StatusCode.WorkerError.value)
        except HTTPException as err:
            self.logger.warning('{}'.format(err))
            # TODO(damb): Return appropiate output message.
            raise err
        except Exception as err:
            self.logger.error('{}'.format(err))
            self.update_state(None)
            return ({'message': str(err),
                     'result': []}, StatusCode.WorkerError.value)

        return ({'message': StatusCode.TaskAccepted.name,
                 'result': []}, StatusCode.TaskAccepted.value)

    # post ()

# class AsyncWorkerResource


# ---- END OF <resource.py> ----
