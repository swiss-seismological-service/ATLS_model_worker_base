# This is <settings.py>
# -----------------------------------------------------------------------------
#
# Purpose: RAMSIS workers component settings
#
# Copyright (c) Daniel Armbruster (SED, ETH), Lukas Heiniger (SED, ETH)
#
# REVISION AND CHANGES
# 2018/04/03        V0.1    Daniel Armbruster
# =============================================================================
"""
General purpose configuration constants.
"""

# -----------------------------------------------------------------------------
# General ramsis worker configuration
# -----------------------------------------------------------------------------
PATH_RAMSIS_WORKER_CONFIG = '/path/to/ramsis_config'
# worker resource URL path
PATH_RAMSIS_WORKER_SCENARIOS = '/runs'

# -----------------------------------------------------------------------------
RAMSIS_WORKER_DB_CONFIG_SECTION = 'CONFIG_WORKER_DB'

# -----------------------------------------------------------------------------
# SaSS worker specific settings
RAMSIS_WORKER_SASS_ID = 'SaSS'
RAMSIS_WORKER_SASS_PORT = 5000
RAMSIS_WORKER_SASS_CONFIG_SECTION = 'CONFIG_WORKER_SASS'

PATH_RAMSIS_SASS_SCENARIOS = ('/' + RAMSIS_WORKER_SASS_ID +
                              PATH_RAMSIS_WORKER_SCENARIOS)

# ---- END OF <settings.py> ----
