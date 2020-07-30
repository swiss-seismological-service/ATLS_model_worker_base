# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
Resource facilities for worker webservices.
"""
import functools
import logging
import uuid

from multiprocessing import Process, Queue
import threading

from flask import request, current_app, g
from flask import make_response as _make_response
from flask_restful import Resource
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import selectinload

from ramsis.sfm.worker import orm
from ramsis.sfm.worker.parser import parser, SFMWorkerIMessageSchema
from ramsis.sfm.worker.task import Task
from ramsis.sfm.worker.utils import (StatusCode, SFMWorkerOMessageSchema,
                                     ResponseData)
from ramsis.utils.error import Error


logger = logging.getLogger("ramsis.sfm.worker.resource")

_HTTP_OK = 200
_HTTP_NO_CONTENT = 204


# -----------------------------------------------------------------------------
class WorkerError(Error):
    """Base worker error ({})."""


class CannotCreateTaskModel(WorkerError):
    """Error while creating task model ({})."""


# -----------------------------------------------------------------------------
def make_response(msg, status_code=None,
                  serializer=SFMWorkerOMessageSchema, **kwargs):
    """
    Factory function creating :py:class:`flask.Flask.response_class.

    :param msg: Serialized message the response is created from :type msg:
    :py:class:`ramsis.sfm.worker.utils.ResponseData` or list of
        :py:class:`ramsis.sfm.worker.utils.ResponseData`
    :param status_code: Force HTTP status code. If :code:`None` the status code
        is extracted from :code:`msg`. If the status code is equal to
        :code:`204: an empty response is returned.
    :type status_code: int or None
    :param serializer: Schema to be used for serialization
    :type serializer: :py:class:`marshmallow.Schema`
    :param kwargs: Keyword value parameters passed to the serializer
    :returns: HTTP response
    :rtype: :py:class:`flask.Flask.response`
    """
    if status_code == _HTTP_NO_CONTENT:
        return '', _HTTP_NO_CONTENT

    try:
        if status_code is None:
            status_code = _HTTP_OK
            try:
                status_code = int(msg.attributes['status_code'])
            except (KeyError, AttributeError):
                if not isinstance(msg, list):
                    raise

        # XXX(damb): Wrap response with data
        msg = dict(data=msg)
        logger.info("about to make respose with serializer")
        resp = _make_response(serializer(**kwargs).dumps(msg), status_code)
        logger.info("finished making response with serializer")

    except Exception as err:
        raise WorkerError(err)

    resp.headers['Content-Type'] = 'application/json'
    return resp


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

            msg = ResponseData.no_content()
            self.logger.debug('Response msg: {}'.format(msg))

            return make_response(msg, status_code=_HTTP_NO_CONTENT)

        return func(self, *args, **kwargs)

    return decorator


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
            f"Received HTTP GET request (task_id: {task_id}).")

        session = self._db.session
        try:
            task = session.query(orm.Task).\
                options(
                    selectinload(orm.Task.result).
                    selectinload(orm.Reservoir.samples).
                    selectinload(orm.ModelResultSample.discretemfd).
                    selectinload(orm.DiscreteMFD.magbins)).\
                options(
                    selectinload(orm.Task.result).
                    selectinload(orm.Reservoir.subgeometries).
                    selectinload(orm.Reservoir.samples).
                    selectinload(orm.ModelResultSample.discretemfd).
                    selectinload(orm.DiscreteMFD.magbins)).\
                options(
                    selectinload(orm.Task.result).
                    selectinload(orm.Reservoir.subgeometries).
                    selectinload(orm.Reservoir.subgeometries)).\
                filter(orm.Task.id == task_id).\
                one()
            msg = ResponseData.from_task(task)
            self.logger.debug(f"Response msg: {msg}")

            return make_response(msg, status_code=_HTTP_OK)

        except NoResultFound:
            return make_response('', status_code=_HTTP_NO_CONTENT)
        except Exception as err:
            session.rollback()
            raise err
        finally:
            session.close()

    @with_validated_args
    def delete(self, task_id):
        """
        Implementation of HTTP :code:`DELETE` method. Removes a specific task.
        """
        self.logger.debug(
            f"Received HTTP DELETE request (task_id: {task_id}).")

        # TODO(damb): To be checked if the task is currently processing.
        session = self._db.session
        try:
            task = session.query(orm.Task).\
                filter(orm.Task.id == task_id).\
                one()

            msg = ResponseData.from_task(task)
            self.logger.debug(f"Response msg: {msg}")

            session.delete(task)
            session.commit()

            return make_response(msg, status_code=_HTTP_OK)

        except NoResultFound:
            return make_response('', status_code=_HTTP_NO_CONTENT)
        except Exception as err:
            session.rollback()
            raise err
        else:
            self.logger.info(
                f"Task (id={task_id}) successfully removed.")
        finally:
            session.close()

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

class LoggerThread:
    def __init__(self, queue):
        self.queue = queue

    def add_process_log(self, queue):
        self.queue = queue
        while True:
            record = self.queue.get()
            if record is None:
                break
            logger = logging.getLogger(record.name)
            logger.handle(record)

class SFMRamsisWorkerListResource(RamsisWorkerBaseResource):
    """
    Implementation of a *stateless* *RT-RAMSIS* seismicity forecast model
    (SFM) worker resource. The resource ships a pool of worker processes.

    By default model results are written to a DB.
    """
    def __init__(self, model, db):
        super().__init__(db=db)

        self._model = model
        self.queue = Queue(-1)
        self.logger_thread = LoggerThread(self.queue)
        self.workers = []

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

            msg = [ResponseData.from_task(t) for t in tasks]

            return make_response(msg, status_code=_HTTP_OK,
                                 serializer=SFMWorkerOMessageSchema)

        except NoResultFound:
            return make_response('', status_code=_HTTP_NO_CONTENT)
        except Exception as err:
            session.rollback()
            raise err
        finally:
            session.close()

    def post(self):
        """
        Implementation of HTTP :code:`POST` method. Maps a task to the
        worker pool.
        """
        self.logger.debug(
            f"Received HTTP POST request (Model: {self._model!r}, "
            f"task_id: {self.request_id})")

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
                filter(orm.Model.name == m_model.name).\
                one_or_none()
            print("Does the model exist?", existing_m_model)

            if existing_m_model:
                m_model = existing_m_model

            m_task = orm.Task.new(id=task_id, model=m_model)

            session.add(m_task)
            session.commit()

        except Exception as err:
            session.rollback()
            raise CannotCreateTaskModel(err)
        else:
            self.logger.debug(
                f"{self!r}: {m_task!r} successfully created.")
        finally:
            session.close()

        self.logger.debug(
            f"Executing {self._model!r} task ({task_id}) "
            f"with parameters {args!r} ...")
        # create a task; inject model_default parameters
        t = Task(
            db_url=current_app.config['SQLALCHEMY_DATABASE_URI'],
            model=self._model(context={'task': task_id},
                              **current_app.config['RAMSIS_SFM_DEFAULTS']),
            queue=self.queue,
            logging_config_path = current_app.config['PATH_LOGGING_CONFIG'],
            log_id=current_app.config['LOG_ID'],
            task_id=task_id, **args['data']['attributes'])

        p = Process(target=t)
        self.workers.append(p)
        self.logger.info(f"Start Process with target={t}")
        p.start()
        lp = threading.Thread(target=self.logger_thread.add_process_log,
                              args=(self.queue,))
        # XXX(damb): Do not call p.join() in order to achieve async behaviour.
        # Instead the DB backend is used to keep data in sync.

        lp.start()
        msg = ResponseData.accepted(task_id)
        self.logger.debug('Task ({}) accepted.'.format(task_id))

        return make_response(msg)

    def _parse(self, request, locations=('json',)):
        """
        Parse the arguments for a model run. Since :code:`model_parameters`
        are implemented as a simple :py:class:`marshmallow.fields.Dict`
        i.e.

        .. code::

            model_parameters =
                marshmallow.fields.Dict(keys=marshmallow.fields.Str())

        by default no validation is performed on model parameters. However,
        overloading this template function and using a model specific
        schema allows the validation of the :code:`model_parameters`
        property.
        """
        return parser.parse(SFMWorkerIMessageSchema(), request,
                            locations=locations)
