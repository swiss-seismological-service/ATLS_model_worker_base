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

from multiprocessing import Pool

from flask import request, current_app, g
from flask import make_response as _make_response
from flask_restful import Resource


from ramsis.utils.error import Error
from ramsis.utils.protocol import (StatusCode, WorkerInputMessageSchema,
                                   WorkerOutputMessage,
                                   WorkerOutputMessageSchema,
                                   MIMETYPE)
from ramsis.worker.utils import orm
from ramsis.worker.utils.task import Task
from ramsis.worker.utils.parser import parser


# -----------------------------------------------------------------------------
class WorkerError(Error):
    """Base worker error ({})."""

class CannotCreateTaskModel(WorkerError):
    """Error while creating task model ({})."""

# -----------------------------------------------------------------------------
def make_response(msg, status_code=None, serializer=WorkerOutputMessageSchema,
                  **kwargs):
    """
    Factory function creating :py:class:`flask.Flask.response_class.

    :param msg: Serialized message the response is created from
    :type msg: :py:class:`ramsis.utils.protocol.WorkerOutputMessage`
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
        raise WorkerError(str(err))

# make_response ()

# -----------------------------------------------------------------------------
class RamsisWorkerBaseResource(Resource):
    """
    Base class for *RT-RAMSIS* worker resources.

    :param db: :py:class:`flask_sqlalchemy.SQLAlchemy` database instance
    :type db: :py:class:`flask_sqlalchemy.SQLAlchemy`
    """

    LOGGER = 'ramsis.worker.worker_resource'

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

class RamsisWorkerResource(RamsisWorkerBaseResource):
    """
    *RT-RAMSIS* worker resource implementation.
    """

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

            msg = WorkerOutputMessage.from_task(task)
            self.logger.debug('Response msg: {}'.format(msg))

            return make_response(msg)

        except Exception as err:
            session.rollback()
            raise err
        finally:
            session.close()

    # get ()

    def delete(self, task_id):
        """
        Implementation of HTTP :code:`DELETE` method. Removes a specific task.
        """
        self.logger.debug(
            'Received HTTP DELETE request (task_id: {}).'.format(task_id))

        session = self._db.session
        try:
            task = session.query(orm.Task).\
                filter(orm.Task.id==task_id).\
                one()

            msg = WorkerOutputMessage.from_task(task)
            self.logger.debug('Response msg: {}'.format(msg))

            session.delete(task)
            session.commit()

            return make_response(msg, status_code=200)

        except Exception as err:
            session.rollback()
            raise err
        finally:
            session.close()

    # delete ()

# class RamsisWorkerResource


class RamsisWorkerListResource(RamsisWorkerBaseResource):
    """
    Implementation of a *stateless* *RT-RAMSIS* worker resource. The resource
    ships a pool of worker processes.

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

            msgs = [WorkerOutputMessage.from_task(t) for t in tasks]
            self.logger.debug('Response msgs: {}'.format(msgs))

            return make_response(msgs, serializer=WorkerOutputMessageSchema,
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

        t = Task(model=self._model(), task_id=task_id,
                 db_url=current_app.config['SQLALCHEMY_DATABASE_URI'], **args)

        # TODO TODO TODO(damb): Register a task @ DB.
        _ = self._pool().apply_async(t) # noqa

        msg = WorkerOutputMessage.accepted(task_id)
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
        return parser.parse(WorkerInputMessageSchema(), request,
                            locations=locations)

    # _parse ()

# class RamsisWorkerListResource


# ---- END OF <resource.py> ----
