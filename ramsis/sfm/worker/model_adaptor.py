# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
General purposes RT-RAMSIS model facilities.
"""

import functools
import logging

from collections import namedtuple

from ramsis.utils.error import Error
from ramsis.sfm.worker.orm import Model as _Model
from ramsis.sfm.worker.utils import (escape_newline, ContextLoggerAdapter,
                                     StatusCode)


class ModelError(Error):
    """Base model error ({})."""


class InvalidConfiguration(ModelError):
    """Invalid configuration ({})."""


# -----------------------------------------------------------------------------
def with_exception_handling(func):
    """
    Method decorator catching unhandled
    :py:class:`ramsis.sfm.worker.model.Model` exceptions. Exceptions are
    wrapped into a valid result.
    """
    @functools.wraps(func)
    def decorator(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as err:
            msg = 'ModelError ({}-{}): {}'.format(type(self).__name__,
                                                  type(err).__name__, err)

            self.logger.critical(escape_newline(msg))
            # XXX(damb): The decorator must return its result in a specific
            # format such that the task both executing the Model and writing
            # the error information to the DB is able to handle the result.
            return ModelResult.error(
                status='ModelError-{}'.format(type(self).__name__),
                status_code=StatusCode.WorkerError.value,
                data=({self.context['task']: msg}
                      if self.context and 'task' in self.context else msg),
                warning='Caught in default model exception handler.')

    return decorator


# -----------------------------------------------------------------------------
class ModelResult(namedtuple('ModelResult',
                             ['status',
                              'status_code',
                              'data',
                              'warning'])):

    @classmethod
    def error(cls, status, status_code, data={}, warning=''):
        return cls(status=status, status_code=status_code, data=data,
                   warning=warning)

    @classmethod
    def ok(cls, data, warning=''):
        return cls(status=StatusCode.TaskCompleted.name,
                   status_code=StatusCode.TaskCompleted.value,
                   data=data, warning=warning)


# -----------------------------------------------------------------------------
class ModelAdaptor(object):
    """
    RT-RAMSIS :py:class:`Model` base class.
    """
    LOGGER = 'ramsis.sfm.worker.model'
    NAME = 'MODEL'
    DESCRIPTION = ''

    def __init__(self, name=None, context={}):
        self.context = context

        self._name = name if name else self.NAME
        self._logger = logging.getLogger(self.LOGGER)
        ctx_logger = ({'ctx': [context['task'], self.name]}
                      if context and 'task' in context else {'ctx': self.name})
        self.logger = ContextLoggerAdapter(self._logger, ctx_logger)

        self._stdout = None
        self._stderr = None

    @classmethod
    def orm(cls):
        return _Model(name=cls.NAME, description=cls.DESCRIPTION)

    @property
    def name(self):
        return self._name

    @property
    def stdout(self):
        return self._stdout

    @property
    def stderr(self):
        return self._stderr

    def _run(self, **kwargs):
        """
        Template method called when running a model *task*. This method
        **must** be implemented by concrete
        :py:class:`ramsis.sfm.worker.utils.Model` implementations.

        Ideally, an instance of :py:class:`ModelResult` is returned to make use
        of data serialization techniques.

        :param kwargs: Model task specific keyword value parameters
        """
        raise NotImplementedError

    @with_exception_handling
    def __call__(self, **kwargs):
        """
        The concept of a *task* is implemented by means of calling or rather
        executing a :py:class:`Model` instance, respectively.

        :param kwargs: Model task specific keyword value parameters
        """
        return self._run(**kwargs)

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
            d['logger'] = ContextLoggerAdapter(
                d['_logger'],
                {'ctx': [d['context']['task'], d['_name']]}
                if d['context'] and 'task' in d['context']
                else {'ctx': d['_name']})
            self.__dict__.update(d)

    def __repr__(self):
        return '<{}(name={})>'.format(type(self).__name__, self.NAME)