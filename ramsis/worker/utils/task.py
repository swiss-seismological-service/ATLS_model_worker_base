# This is <task.py>
# -----------------------------------------------------------------------------
#
# Purpose: Provide an ABC for a Task.
#
# Copyright (c) Daniel Armbruster (SED, ETH), Lukas Heiniger (SED, ETH)
#
# REVISION AND CHANGES
# 2018/04/10        V0.1    Daniel Armbruster
# =============================================================================
"""
Task facilities.
"""

import logging

from ramsis.utils.error import Error


# -----------------------------------------------------------------------------
class TaskError(Error):
    """Base task error ({})."""

class NotConfigured(TaskError):
    """Missing task configuration."""

class InvalidConfiguration(TaskError):
    """Invalid configuration ({})."""


class TaskStream(object):
    """ABC for stream task stream objects."""

    def __str__(self):
        return ''


# -----------------------------------------------------------------------------
class Task(object):
    """
    Abstract base class for a task.
    """

    LOGGER = 'ramsis.worker.task'

    def __init__(self, logger=None):
        self.is_configured = False
        self._stdout = None
        self._stderr = None

        self.logger = (logging.getLogger(logger) if logger else
                       logging.getLogger(self.LOGGER))

    # __init__ ()

    @property
    def result(self):
        """Task result query function."""
        raise NotImplementedError

    @property
    def returncode(self):
        """Task returncode query function."""
        raise NotImplementedError

    @property
    def stdout(self):
        return None

    @property
    def stderr(self):
        return None

    def poll(self):
        """
        Poll the status of a task. For a synchronous task the function
        should always return `None`.
        """
        return None

    def configure(self, **kwargs):
        """
        Configure a task.

        :param **kwargs: Function keyword arguments passed to the
        function to be called.
        """
        raise NotImplementedError

    def reset(self):
        """
        Reininitialize a task.
        """
        raise NotImplementedError

    def _run(self):
        """
        Run a task.
        """
        raise NotImplementedError

    def __call__(self):
        self._run()

# class Task


class AsyncTask(Task):
    """
    Abstract base class for an asynchronous task.
    """

    LOGGER = 'ramsis.worker.asnyc_task'

    def __init__(self, logger=None):
        self._result = None
        self._process = None
        self._returncode = None

        super().__init__(logger=logger if logger is not None else self.LOGGER)

    @property
    def returncode(self):
        return self._returncode

    def reset(self):
        if self.is_configured:
            self._process = None
            self._result = None
            self._returncode = None
            self._stdout = None
            self._stderr = None
            self.is_configured = False

    def poll(self):
        raise NotImplementedError

# class AsyncTask

# ---- END OF <task.py> ----
