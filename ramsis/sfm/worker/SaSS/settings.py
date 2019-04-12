# This is <settings.py>
# -----------------------------------------------------------------------------
#
# REVISION AND CHANGES
# 2019/02/22        V0.1    Daniel Armbruster
# =============================================================================
"""
General purpose configuration constants.
"""
from ramsis.sfm.worker import settings
from ramsis.sfm.worker.SaSS.core import (DEFAULT_DIM_VOXEL, DEFAULT_NUM_KERNELS)

RAMSIS_WORKER_SASS_ID = 'SaSS'
RAMSIS_WORKER_SASS_PORT = 5000
RAMSIS_WORKER_SASS_CONFIG_SECTION = 'CONFIG_WORKER_SASS'

PATH_RAMSIS_SASS_SCENARIOS = ('/' + RAMSIS_WORKER_SASS_ID +
                              settings.PATH_RAMSIS_WORKER_SCENARIOS)

# TODO(damb): Configure meaningful defaults
RAMSIS_WORKER_SFM_DEFAULTS = {
    # XXX(damb): Reservoir description (format=WKT, srid=4326)
    "reservoir": {"geom": ('POLYHEDRALSURFACE Z ('
                           '((0 0 0, 0 1 0, 1 1 0, 1 0 0, 0 0 0)),'
                           '((0 0 0, 0 1 0, 0 1 1, 0 0 1, 0 0 0)),'
                           '((0 0 0, 1 0 0, 1 0 1, 0 0 1, 0 0 0)),'
                           '((1 1 1, 1 0 1, 0 0 1, 0 1 1, 1 1 1)),'
                           '((1 1 1, 1 0 1, 1 0 0, 1 1 0, 1 1 1)),'
                           '((1 1 1, 1 1 0, 0 1 0, 0 1 1, 1 1 1)))')},
    "model_parameters": {
        # XXX(damb): Local spatial reference system (SRS) spatial data is
        # transformed into (format=Proj4)
        "local_srs": '',
        "const_dim_voxel": DEFAULT_DIM_VOXEL,
        "training_duration": 6.0,
        "training_num_kernels": DEFAULT_NUM_KERNELS,
        "fc_threshold_magnitude": 2.6,
        "fc_cumulative_injected_volume": 0}}

# ---- END OF <settings.py> ----
