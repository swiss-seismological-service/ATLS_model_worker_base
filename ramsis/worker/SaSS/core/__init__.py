# This is <__init__.py>
# ----------------------------------------------------------------------------
#
# Copyright (c) 2018 by Daniel Armbruster (SED, ETHZ)
#
#
# REVISIONS and CHANGES
# 2018/10/08    V1.0   Daniel Armbruster
#
# ============================================================================
"""
Python package providing an implementation of the SaSS (`Shapiro and Smoothed
Seismicity <https://library.seg.org/doi/10.1190/1.3353727>`_) model.

.. note::

    This implementation is based on the work of Eszter Kiraly (2014).
    Originally, the model was implemented by her using `MATLAB
    <https://www.mathworks.com/products/matlab.html>`_.


**Usage**:

.. code::

    TODO

"""

import collections
import datetime


# FIXME(damb): To be moved to core.utils; check for circular deps
BandwidthConfig = collections.namedtuple('BandwidthConfig',
                                         ['bandwidth_min',
                                          'trustlevel_min',
                                          'bandwidth_max',
                                          'trustlevel_max'])

# -----------------------------------------------------------------------------
# General purpose constants
# ---
# Default voxel dimensions in meters (dim-x, dim-y, dim-z)
DEFAULT_DIM_VOXEL = (200, 200, 200)

# -----------------------------------------------------------------------------
# Training specific constants
# ---
# Training duration in days
DEFAULT_TRAINING_DURATION = 12/24.

DEFAULT_NUM_KERNELS = 1000

DEFAULT_KERNEL_BANDWIDTH_CONFIG = BandwidthConfig(
    bandwidth_min=5,
    trustlevel_min=99,
    bandwidth_max=400,
    trustlevel_max=1)

# -----------------------------------------------------------------------------
# Forecast specific constants
# ---
# Forecast duration in days
DEFAULT_FORECAST_DURATION = 6/24.
# Datetime the forecast is started
DEFAULT_FORECAST_START = datetime.datetime.utcnow()

# Hysteresis: Total number of earthquakes from previous forcast periods
DEFAULT_HYSTERESIS_TOTAL_NUM_EQ = 0

# Maximum magnitude to be allowed during a forcast
DEFAULT_MAG_MAX = 5
# Magnitude binning constant
DEFAULT_MAG_BINNING = 0.1

DEFAULT_THRESHOLD_STIMULATION = 0.001

DEFAULT_TEMPORAL_WEIGHT = None


# ---- END OF <__init__.py> ----
