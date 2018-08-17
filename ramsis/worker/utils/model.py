# This is <model.py>
# -----------------------------------------------------------------------------
#
# Purpose: General purposes RT-RAMSIS model facilities.
#
# Copyright (c) Daniel Armbruster (SED, ETH), Lukas Heiniger (SED, ETH)
#
# REVISION AND CHANGES
# 2018/08/14        V0.1    Daniel Armbruster
# =============================================================================
"""
General purposes RT-RAMSIS model facilities.
"""

import functools
import logging

from ramsis.utils.error import Error
from ramsis.utils.protocol import (WorkerOutputMessage as ModelResult,
                                   StatusCode)
from ramsis.worker.utils import escape_newline
from ramsis.worker.utils.orm import Model as _Model


class ModelError(Error):
    """Base model error ({})."""

class InvalidConfiguration(ModelError):
    """Invalid configuration ({})."""

# -----------------------------------------------------------------------------
def with_exception_handling(func):
    """
    Method decorator catching unhandled :py:class:`ramsis.worker.utils.Model`
    exceptions. Exceptions are wrapped into a valid result.
    """
    @functools.wraps(func)
    def decorator(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as err:
            msg = 'ModelError ({}): {}: {}.'.format(type(self).__name__,
                                                    type(err).__name__, err)

            self.logger.critical(escape_newline(msg))
            # XXX(damb): The decorator must return its result in a specific
            # format such that the task both executing the Model and writing
            # the error information to the DB is able to handle the result.
            task_id = args[0] if args else kwargs.get('task_id')
            return ModelResult.error(
                status='ModelError-{}'.format(type(self).__name__),
                status_code=StatusCode.WorkerError.value,
                data={task_id: msg},
                warning='Caught in default model exception handler.')

    return decorator

# with_exception_handling ()

# -----------------------------------------------------------------------------
class Model(object):
    """
    RT-RAMSIS :py:class:`Model` base class.
    """
    LOGGER = 'ramsis.worker.model'
    NAME = 'MODEL'
    DESCRIPTION = ''

    def __init__(self):
        self.logger = logging.getLogger(self.LOGGER)

        self._stdout = None
        self._stderr = None

    # __init__ ()

    @classmethod
    def orm(cls):
        return _Model(name=cls.NAME, description=cls.DESCRIPTION)

    @property
    def stdout(self):
        return str(self._stdout)

    @property
    def stderr(self):
        return str(self._stderr)

    def _run(self, task_id, **kwargs):
        """
        Template method called when running a model *task*. This method
        **must** be implemented by concrete
        :py:class:`ramsis.worker.utils.Model` implementations.

        Ideally, an instance of :py:class:`ModelResult` is returned to make use
        of data serialization techniques.

        :param task_id: Task identifier
        :type task_id: :py:class:`uuid.UUID`
        :param kwargs: Model task specific keyword value parameters
        """
        raise NotImplementedError

    # _run ()

    @with_exception_handling
    def __call__(self, task_id, **kwargs):
        """
        The concept of a *task* is implemented by means of calling or rather
        executing a :py:class:`Model` instance, respectively.

        :param task_id: Task identifier
        :type task_id: :py:class:`uuid.UUID`
        :param kwargs: Model task specific keyword value parameters
        """
        return self._run(task_id, **kwargs)

    # __call__ ()

    def __getstate__(self):
        # prevent pickling errors for loggers
        d = dict(self.__dict__)
        if 'logger' in d.keys():
            d['logger'] = d['logger'].name
        return d

    # __getstate__ ()

    def __setstate__(self, d):
        if 'logger' in d.keys():
            d['logger'] = logging.getLogger(d['logger'])
            self.__dict__.update(d)

    # __setstate__ ()

    def __repr__(self):
        return '<{}(name={})'.format(type(self).__name__, self.NAME)

# class Model


# ---- END OF <model.py> ----
