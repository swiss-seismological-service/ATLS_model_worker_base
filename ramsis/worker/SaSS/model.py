# This is <model.py>
# -----------------------------------------------------------------------------
#
# Purpose: SaSS model facilities.
#
# Copyright (c) Daniel Armbruster (SED, ETH)
#
# REVISION AND CHANGES
# 2018/08/14        V0.1    Daniel Armbruster
# =============================================================================
"""
*SaSS* (`Shapiro and Smoothed Seismicity
<https://library.seg.org/doi/10.1190/1.3353727>`_) model facilities.
"""
import io

import matlab.engine

from ramsis.worker.utils import orm
from ramsis.worker.utils.model import (Model as _Model, ModelError,
                                       ModelResult, InvalidConfiguration)


class MatlabError(ModelError):
    """Matlab base error ({})."""

class InvalidMatlabFunction(MatlabError):
    """No corresponding MATLAB function found ({})."""


# -----------------------------------------------------------------------------
class Model(_Model):
    """
    Dummy SaSS model implementation. Wrapping the actual model implementation
    written in `MATLAB <https://www.mathworks.com/products/matlab.html>`_. The
    wrapper makes use of the `MATLAB API for Python
    <https://ch.mathworks.com/help/matlab/matlab-engine-for-python.html>`_.

    :param str matlab_opts: String of initialization arguments passed to
        :py:func:`matlab.engine.start_matlab`.
    """

    LOGGER = 'ramsis.worker.model_sass'
    MATLAB_FUNC = 'SaSS'
    MATLAB_FUNC_NARGOUT = 1

    NAME = 'SaSS'
    DESCRIPTION = 'Shapiro and Smoothed Seismicity'

    class TaskStream(io.StringIO):

        def __str__(self):
            try:
                return self.getvalue()
            except Exception:
                return ''

    # class TaskStream

    def __init__(self, matlab_opts=''):
        super().__init__()
        self._matlab_opts = matlab_opts

    @property
    def stdout(self):
        return str(self._stdout)

    @property
    def stderr(self):
        return str(self._stderr)

    def _run(self, task_id, **kwargs):
        """
        :param kwargs: Model task specific keyword value parameters. Parameters
            are orderedly passed to the actual `MATLAB
        <https://ch.mathworks.com/products/matlab.html>`_ SaSS model
        implementation.
        """
        self.logger.debug('{!r}: Running model ...'.format(self))

        # XXX(damb): Order configuration parameters. # TODO TODO TODO
        try:
            reservoir_geom = kwargs['reservoir_geometry']
            func_args = kwargs['model_parameters'].values()
        except KeyError as err:
            raise InvalidConfiguration(err)

        self.logger.debug(
            '{}: reservoir_geometry={}, model_parameters={}'.format(
                self, reservoir_geom, func_args))

        try:
            engine = matlab.engine.start_matlab(self._matlab_opts)

            try:
                matlab_func = getattr(engine, self.MATLAB_FUNC)
            except AttributeError as err:
                raise InvalidMatlabFunction(err)

            self._stdout = self.TaskStream()
            self._stderr = self.TaskStream()

            try:
                result = matlab_func(*func_args,
                                     nargout=self.MATLAB_FUNC_NARGOUT,
                                     stdout=self._stdout,
                                     stderr=self._stderr)

                return ModelResult.ok(
                    data={task_id: orm.Reservoir(geom=reservoir_geom,
                                                 b_value=result)},
                    warning=self.stderr if self.stderr else self.stdout)

            except matlab.engine.MatlabExecutionError as err:
                self.logger.error(self.stderr)
                raise MatlabError(err)

        finally:
            try:
                engine.quit()
            except NameError:
                pass

    # _run ()

# class SaSSModel

# ---- END OF <model.py> ----
