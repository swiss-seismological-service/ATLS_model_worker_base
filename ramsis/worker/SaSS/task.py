# This is <task.py>
# -----------------------------------------------------------------------------
#
# Purpose: SaSS task facilities. Task implementation of the SaSS model.
#
# Copyright (c) Daniel Armbruster (SED, ETH), Lukas Heiniger (SED, ETH)
#
# REVISION AND CHANGES
# 2018/04/12        V0.1    Daniel Armbruster
# =============================================================================
"""
SaSS (Shapiro and Smothed Seismicity) task facilities.
"""

import io

import matlab.engine

from ramsis.worker.utils.task import (AsyncTask, TaskStream, TaskError,
                                      NotConfigured,
                                      InvalidConfiguration)


class InvalidMatlabFunction(TaskError):
    """No corresponding MATLAB function found ({})."""

class MatlabError(TaskError):
    """MATLAB error ({})."""


class SaSSTaskStream(io.StringIO, TaskStream):

    def __str__(self):
        try:
            return self.getvalue()
        except Exception:
            return ''

# class SaSSTaskStream

# -----------------------------------------------------------------------------
class SaSSTask(AsyncTask):
    """
    Concrete implementation of a task managing the *SaSS* model. The task is
    implemented as an asynchronous MATLAB task.

    The task currently makes use of the `MATLAB Python API
    <https://www.mathworks.com/help/matlab/matlab-engine-for-python.html>`_.

    :param str matlab_func: MATLAB function to be called.
    """

    LOGGER = 'ramsis.worker.sass_task'

    def __init__(self, matlab_func, func_nargout=1, matlab_opts=''):
        super().__init__()
        self.engine = matlab.engine.start_matlab(matlab_opts)
        self._func = matlab_func
        self._func_nargout = func_nargout
        self._func_args = None

    # __init__ ()

    @property
    def result(self):
        return self._result

    @property
    def stdout(self):
        return self._stdout

    @property
    def stderr(self):
        return self._stderr

    def configure(self, **kwargs):
        """
        Configure a task.
        """
        if not self.is_configured:
            # TODO(damb): The task has to order the kwargs and add it to the
            # _func_args list appropriately. This behaviour is MATLAB specific.
            try:
                self._func_args = kwargs.values()
            except KeyError as err:
                raise InvalidConfiguration(err)

            self.is_configured = True

    # configure ()

    def poll(self):
        if self._process and self._process.done():
            self._result = self._process.result()
            self._returncode = 0
            return self.returncode
        return None

    # poll ()

    def _run(self):
        if not self.is_configured:
            raise NotConfigured()

        try:
            matlab_func = getattr(self.engine, self._func)
        except AttributeError as err:
            raise InvalidMatlabFunction(err)

        # NOTE(damb): Due to the fact that the task is run asynchronously
        # capturing exceptions is not possible.
        self._stdout = SaSSTaskStream()
        self._stderr = SaSSTaskStream()
        self._process = matlab_func(*self._func_args,
                                    nargout=self._func_nargout,
                                    async=True,
                                    stdout=self._stdout,
                                    stderr=self._stderr)

    # _run ()

# class SaSSTask

# ---- END OF <task.py> ----
