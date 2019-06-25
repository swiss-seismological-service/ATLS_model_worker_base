# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
Task facilities.
"""

import functools
import logging
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ramsis.utils.error import ErrorWithTraceback
from ramsis.sfm.worker import orm
from ramsis.sfm.worker.utils import escape_newline, StatusCode


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
    # TODO(damb): Avoid repeating string content.
    @functools.wraps(func)
    def decorator(self, *args, **kwargs):

        _model = self._model
        self.logger.debug('{!r}: Executing {!r} (args={}, kwargs={})'.format(
            self, _model, self._task_id, kwargs))
        retval = func(self, *args, **kwargs)
        self.logger.debug(
            '{!r}: {!r} execution finished (result={})).'.format(
                self, _model, retval))

        if _model.stdout:
            self.logger.info(escape_newline('{!r}: STDOUT ({!r}): {}'.format(
                self, _model, _model.stdout)))
        if _model.stderr:
            self.logger.warning(
                escape_newline('{!r}: STDERR ({}): {}'.format(
                    self, _model, _model.stderr)))

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
        self.logger = logging.getLogger(self.LOGGER)

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
        if 'logger' in d.keys():
            d['logger'] = d['logger'].name
        return d

    def __setstate__(self, d):
        if 'logger' in d.keys():
            d['logger'] = logging.getLogger(d['logger'])
            self.__dict__.update(d)

    @with_logging
    def _run(self, **kwargs):
        """
        Execute a model with a concrete parameter configuration.

        :param kwargs: Extra keyword value parameters passed to the
            :py:class:`ramsis.sfm.worker.utils.Model` instance, additionally.
        """
        return self._model(task_id=self.id, **self._task_args, **kwargs)

    @with_exception_handling
    def __call__(self, **kwargs):

        def create_session(db_engine):
            return sessionmaker(bind=db_engine)()

        db_engine = create_engine(self._db_url)
        session = create_session(db_engine)
        # XXX(damb): fetch orm.Task from DB and update task state
        try:
            m_task = session.query(orm.Task).\
                filter(orm.Task.id == self.id).\
                one()

            m_task.status = StatusCode.TaskProcessing.name
            m_task.status_code = StatusCode.TaskProcessing.value

            session.commit()

        except Exception as err:
            session.rollback()
            raise NoTaskModel(err)
        finally:
            session.close()

        retval = self._run(**kwargs)

        session = create_session(db_engine)
        try:
            self.logger.debug(
                '{!r}: Writing results to DB (db_url={}) ...'.format(
                    self, self._db_url))

            m_task = session.query(orm.Task).\
                filter(orm.Task.id == self.id).\
                one()

            m_task.status = retval.status
            m_task.status_code = retval.status_code
            m_task.warning = retval.warning

            if retval.status_code == 200:
                m_task.result = retval.data[self.id]

            session.commit()
            self.logger.debug(
                '{!r}: {!r} successfully written.'.format(self, m_task))

            return retval

        except Exception as err:
            session.rollback()
            raise err
        finally:
            session.close()

    def __repr__(self):
        return '<{}(id={})>'.format(type(self).__name__, self.id)
