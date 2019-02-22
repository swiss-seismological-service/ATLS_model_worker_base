# This is <settings.py>
# -----------------------------------------------------------------------------
#
# REVISION AND CHANGES
# 2019/02/22        V0.1    Daniel Armbruster
# =============================================================================
"""
General purpose configuration constants.
"""
from ramsis.worker import settings
from ramsis.worker.SaSS.core import (DEFAULT_DIM_VOXEL, DEFAULT_NUM_KERNELS)

RAMSIS_WORKER_SASS_ID = 'SaSS'
RAMSIS_WORKER_SASS_PORT = 5000
RAMSIS_WORKER_SASS_CONFIG_SECTION = 'CONFIG_WORKER_SASS'

PATH_RAMSIS_SASS_SCENARIOS = ('/' + RAMSIS_WORKER_SASS_ID +
                              settings.PATH_RAMSIS_WORKER_SCENARIOS)

# TODO(damb): Configure meaningful defaults
RAMSIS_WORKER_SFM_DEFAULTS = {
    "model_parameters": {
        "const_dim_voxel": DEFAULT_DIM_VOXEL,
        "training_duration": 6.0,
        "training_num_kernels": DEFAULT_NUM_KERNELS,
        "fc_threshold_magnitude": 2.6,
        "fc_cumulative_injected_volume": 0}}

# ---- END OF <settings.py> ----
