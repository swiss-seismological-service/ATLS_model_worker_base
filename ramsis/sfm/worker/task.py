# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
Task facilities.
"""

import functools
import logging
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from ramsis.utils.error import ErrorWithTraceback
from ramsis.sfm.worker import orm
from ramsis.sfm.worker.utils import (escape_newline, ContextLoggerAdapter,
                                     StatusCode)


# -----------------------------------------------------------------------------
class TaskError(ErrorWithTraceback):
    """Base task error ({})."""


class NoTaskModel(TaskError):
    """Task model not available ({})."""


# -----------------------------------------------------------------------------
def with_exception_handling(func):
    """
    Method decorator catching unhandled
    :py:class:`ramsis.sfm.worker.utils.Task` exceptions. Exceptions are simply
    logged.
    """
    @functools.wraps(func)
    def decorator(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as err:
            msg = 'TaskError ({}): {}:{}.'.format(type(self).__name__,
                                                  type(err).__name__, err)

            self.logger.critical(escape_newline(msg))

    return decorator


def with_logging(func):
    """
    Method decorator logging the :py:class:`Model`'s state.
    """
    @functools.wraps(func)
    def decorator(self, *args, **kwargs):

        _model = self._model
        self.logger.debug(
            f"Executing {_model} "
            f"(args={self._task_id}, kwargs={kwargs}) ...")
        retval = func(self, *args, **kwargs)
        self.logger.debug(
            f"{_model!r} execution finished (result={retval})).")

        if _model.stdout:
            self.logger.info(escape_newline(
                f"STDOUT {_model!r}: {_model.stdout}"))
        if _model.stderr:
            self.logger.warning(escape_newline(
                f"STDERR {_model!r}: {_model.stderr}"))

        return retval

    return decorator


# -----------------------------------------------------------------------------
class Task(object):
    """
    :py:class:`Task` implementation running
    :py:class:`ramsis.sfm.worker.utils.model.Model`s. Provides a top-level
    class for easier pickling. In addition acts as a controller for the task's
    *actual* model (not to be confused with the scientific model).

    :py:class:`ramsis.sfm.worker.utils.model.ModelResult`s are written to a
    database.

    :param model: :py:class:`ramsis.sfm.worker.utils.Model` instance to be run
    :type model: :py:class:`ramsis.sfm.worker.utils.Model`
    :param db_session: Database session instance
    :type db_session: :py:class:`sqlalchemy.orm.session.Session`
    :param task_id: Task identifier
    :type task_id: :py:class:`ùuid.UUID`
    :param kwargs: Keyword value parameters used when running the
        :py:class:`ramsis.sfm.worker.utils.model.Model`.
    """

    LOGGER = 'ramsis.sfm.worker.task'

    def __init__(self, model, db_url, task_id=None, **kwargs):
        self._logger = logging.getLogger(self.LOGGER)
        self.logger = ContextLoggerAdapter(self._logger, {'ctx': task_id})

        self._model = model
        self._db_url = db_url
        self._task_id = task_id if task_id is not None else uuid.uuid4()
        self._task_args = kwargs

    @property
    def id(self):
        return self._task_id

    def __getstate__(self):
        # prevent pickling errors for loggers
        d = dict(self.__dict__)
        if '_logger' in d.keys():
            d['_logger'] = d['_logger'].name
        if 'logger' in d.keys():
            del d['logger']
        return d

    def __setstate__(self, d):
        if '_logger' in d.keys():
            d['_logger'] = logging.getLogger(d['_logger'])
            d['logger'] = ContextLoggerAdapter(d['_logger'],
                                               {'ctx': d['_task_id']})
            self.__dict__.update(d)

    @with_logging
    def _run(self, **kwargs):
        """
        Execute a model with a concrete parameter configuration.

        :param kwargs: Extra keyword value parameters passed to the
            :py:class:`ramsis.sfm.worker.utils.Model` instance, additionally.
        """
        return self._model(**self._task_args, **kwargs)

    @with_exception_handling
    def __call__(self, **kwargs):

        def create_session(db_engine):
            return sessionmaker(bind=db_engine)()

        def task_from_db(session, task_id):
            return session.query(orm.Task).\
                filter(orm.Task.id == task_id).\
                one()

        db_engine = create_engine(self._db_url)
        session = create_session(db_engine)
        m_task_available = True
        # XXX(damb): fetch orm.Task from DB and update task state
        try:
            m_task = task_from_db(session, self.id)
            m_task.status = StatusCode.TaskProcessing.name
            m_task.status_code = StatusCode.TaskProcessing.value

            session.commit()

        except NoResultFound as err:
            self.logger.warning(
                f"Task unavailable ({err}). Nothing to be done.")
            m_task_available = False
        except Exception as err:
            session.rollback()
            raise NoTaskModel(err)
        finally:
            session.close()

        if not m_task_available:
            return None

        retval = self._run(**kwargs)

        self.logger.debug(
            f"Writing results to DB (db_url={self._db_url}) ...")
        session = create_session(db_engine)
        try:
            m_task = task_from_db(session, self.id)
            m_task.status = retval.status
            m_task.status_code = retval.status_code
            m_task.warning = retval.warning

            if retval.status_code == 200:
                m_task.result = (retval.data[self.id]
                                 if self.id in retval.data else retval.data)

            session.commit()

        except NoResultFound as err:
            self.logger.warning(
                f"Task unavailable ({err}). Unable to write results.")
        except Exception as err:
            session.rollback()
            raise err
        else:
            self.logger.debug(f"Task successfully written.")
        finally:
            session.close()

        return None

    def __repr__(self):
        return '<{}(id={})>'.format(type(self).__name__, self.id)
