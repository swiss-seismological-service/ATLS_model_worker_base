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

import functools
import logging
import uuid

from multiprocessing import Pool

from flask import request, current_app, g
from flask import make_response as _make_response
from flask_restful import Resource
from sqlalchemy.orm.exc import NoResultFound

from ramsis.utils.error import Error
from ramsis.utils.protocol import (StatusCode, SFMWorkerInputMessageSchema,
                                   SFMWorkerOutputMessage,
                                   SFMWorkerOutputMessageSchema,
                                   MIMETYPE)
from ramsis.sfm.worker import orm
from ramsis.sfm.worker.task import Task
from ramsis.sfm.worker.parser import parser


# -----------------------------------------------------------------------------
class WorkerError(Error):
    """Base worker error ({})."""

class CannotCreateTaskModel(WorkerError):
    """Error while creating task model ({})."""

# -----------------------------------------------------------------------------
def make_response(msg, status_code=None,
                  serializer=SFMWorkerOutputMessageSchema, **kwargs):
    """
    Factory function creating :py:class:`flask.Flask.response_class.

    :param msg: Serialized message the response is created from
    :type msg: :py:class:`ramsis.utils.protocol.SFMWorkerOutputMessage`
    :param status_code: Force HTTP status code. If :code:`None` the status code
        is extracted from :code:`msg`
    :type status_code: int or None
    :param serializer: Schema to be used for serialization
    :type serializer: :py:class:`marshmallow.Schema`
    :param kwargs: Keyword value parameters passed to the serializer
    :returns: HTTP response
    :rtype: :py:class:`flask.Flask.response`
    """
    try:
        if status_code is None:
            status_code = 200
            try:
                status_code = int(msg.status_code)
            except AttributeError:
                if not isinstance(msg, list):
                    raise

        resp = _make_response(serializer(**kwargs).dumps(msg), status_code)
        resp.headers['Content-Type'] = MIMETYPE
        #if msg.warning:
        #    resp.headers['Warning'] = '299 {}'.format(msg.warning)
        return resp

    except Exception as err:
        raise WorkerError(err)

# make_response ()


def with_validated_args(func):
    """
    Method decorator providing a generic argument validation.
    """
    @functools.wraps(func)
    def decorator(self, *args, **kwargs):
        try:
            _ = self.validate_args(kwargs.get('task_id'))  # noqa
        except ValueError as err:
            self.logger.warning('Invalid argument: {}.'.format(err))

            msg = SFMWorkerOutputMessage.no_content(kwargs.get('task_id'))
            self.logger.debug('Response msg: {}'.format(msg))

            return make_response(msg)

        return func(self, *args, **kwargs)

    return decorator

# with_validated_args ()


# -----------------------------------------------------------------------------
class RamsisWorkerBaseResource(Resource):
    """
    Base class for *RT-RAMSIS* worker resources.

    :param db: :py:class:`flask_sqlalchemy.SQLAlchemy` database instance
    :type db: :py:class:`flask_sqlalchemy.SQLAlchemy`
    """

    LOGGER = 'ramsis.sfm.worker.worker_resource'

    def __init__(self, db):
        self.logger = logging.getLogger(self.LOGGER)
        self._db = db

    def get(self):
        return 'Method not allowed.', StatusCode.HTTPMethodNotAllowed.value

    def post(self):
        return 'Method not allowed.', StatusCode.HTTPMethodNotAllowed.value

    def delete(self):
        return 'Method not allowed.', StatusCode.HTTPMethodNotAllowed.value

# class RamsisWorkerBaseResource

class SFMRamsisWorkerResource(RamsisWorkerBaseResource):
    """
    *RT-RAMSIS* seismicity forecast model (SFM) worker resource implementation.
    """

    @with_validated_args
    def get(self, task_id):
        """
        Implementation of HTTP :code:`GET` method. Returns a specific task.
        """
        self.logger.debug(
            'Received HTTP GET request (task_id: {}).'.format(task_id))

        session = self._db.session
        try:
            task = session.query(orm.Task).\
                filter(orm.Task.id==task_id).\
                one()

            msg = SFMWorkerOutputMessage.from_task(task)
            self.logger.debug('Response msg: {}'.format(msg))

        except Exception as err:
            session.rollback()
            raise err
        finally:
            session.close()

        return make_response(msg)

    # get ()

    @with_validated_args
    def delete(self, task_id):
        """
        Implementation of HTTP :code:`DELETE` method. Removes a specific task.
        """
        self.logger.debug(
            'Received HTTP DELETE request (task_id: {}).'.format(task_id))

        # TODO(damb): To be checked if the task is currently processing.
        session = self._db.session
        try:
            task = session.query(orm.Task).\
                filter(orm.Task.id==task_id).\
                one()

            msg = SFMWorkerOutputMessage.from_task(task)
            self.logger.debug('Response msg: {}'.format(msg))

            session.delete(task)
            session.commit()

            return make_response(msg, status_code=200)

        except NoResultFound as err:
            self.logger.warning(
                'No matching task found (id={}).'.format(task_id))

            msg = SFMWorkerOutputMessage.no_content(task_id)
            self.logger.debug('Response msg: {}'.format(msg))
            return make_response(msg)

        except Exception as err:
            session.rollback()
            raise err
        finally:
            session.close()

    # delete ()

    @staticmethod
    def validate_args(task_id):
        """
        Validate resource arguments.

        :param str task_id: Task identifier (must be :py:class:`uuid.UUID`
            compatible)

        :return: Task identifier
        :rtype: :py:class:`uuid.UUID`

        :raises ValueError: If an invalid value is passed
        """
        return uuid.UUID(task_id)

    # validate_args ()

# class SFMRamsisWorkerResource


class SFMRamsisWorkerListResource(RamsisWorkerBaseResource):
    """
    Implementation of a *stateless* *RT-RAMSIS* seismicity forecast model (SFM)
    worker resource. The resource ships a pool of worker processes.

    By default model results are written to a DB.
    """
    POOL = Pool(processes=5)

    def __init__(self, model, db):
        super().__init__(db=db)

        self._model = model

    # __init__ ()

    @classmethod
    def _pool(cls):
        if cls.POOL is None:
            raise WorkerError('POOL undefined.')
        return cls.POOL

    @property
    def request_id(self):
        if getattr(g, 'request_id', None):
            return g.request_id
        raise KeyError("Missing key 'request_id' in application context.")

    def get(self):
        """
        Implementation of HTTP :code:`GET` method. Returns all available
        tasks.
        """
        self.logger.debug('Received HTTP GET request.')

        session = self._db.session
        try:
            tasks = session.query(orm.Task).\
                all()

            msgs = [SFMWorkerOutputMessage.from_task(t) for t in tasks]
            self.logger.debug('Response msgs: {}'.format(msgs))

            return make_response(msgs, serializer=SFMWorkerOutputMessageSchema,
                                 many=True)

        except Exception as err:
            session.rollback()
            raise err
        finally:
            session.close()

    # get ()

    def post(self):
        """
        Implementation of HTTP :code:`POST` method. Maps a task to the worker
        pool.
        """
        self.logger.debug(
            'Received HTTP POST request (Model: {!r}, task_id: {}).'.format(
                self._model, self.request_id))

        # parse arguments
        args = self._parse(request, locations=('json',))

        task_id = self.request_id
        # XXX(damb): register a new orm.Task at DB
        session = self._db.session
        try:
            # XXX(damb): create a new orm.Model if not existant
            m_model = self._model.orm()
            existing_m_model = \
                session.query(orm.Model).\
                filter(orm.Model.name==m_model.name).\
                filter(orm.Model.description==m_model.description).\
                one_or_none()

            if existing_m_model:
                m_model = existing_m_model

            m_task = orm.Task.new(id=task_id, model=m_model)

            session.add(m_task)
            session.commit()

            self.logger.debug(
                '{!r}: {!r} successfully created.'.format(self, m_task))
        except Exception as err:
            session.rollback()
            raise CannotCreateTaskModel(err)
        finally:
            session.close()

        self.logger.debug(
            'Executing {!r} task ({}) with parameters {!r} ...'.format(
                self._model, task_id, args))

        # create a task; inject model_default parameters
        t = Task(
            model=self._model(**current_app.config['RAMSIS_SFM_DEFAULTS']),
            task_id=task_id,
            db_url=current_app.config['SQLALCHEMY_DATABASE_URI'], **args)

        _ = self._pool().apply_async(t) # noqa

        msg = SFMWorkerOutputMessage.accepted(task_id)
        self.logger.debug('Task ({}) accepted.'.format(task_id))

        return make_response(msg)

    # post ()

    def _parse(self, request, locations=('json',)):
        """
        Parse the arguments for a model run. Since :code:`model_parameters` are
        implemented as a simple :py:class:`marshmallow.fields.Dict` i.e.

        .. code::

            model_parameters =
                marshmallow.fields.Dict(keys=marshmallow.fields.Str())

        by default no validation is performed on model parameters. However,
        overloading this template function and using a model specific schema
        allows the validation of the :code:`model_parameters` property.
        """
        return parser.parse(SFMWorkerInputMessageSchema(), request,
                            locations=locations)

    # _parse ()

# class SFMRamsisWorkerListResource


# ---- END OF <resource.py> ----
