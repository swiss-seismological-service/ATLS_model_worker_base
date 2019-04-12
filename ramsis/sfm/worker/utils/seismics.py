# This is <seismics.py>
# -----------------------------------------------------------------------------
#
# Purpose: Worker utilities related to seismology.
#
# Copyright (c) Daniel Armbruster (SED, ETH)
#
# REVISION AND CHANGES
# 2018/10/11        V0.1    Daniel Armbruster
# =============================================================================
"""
RAMSIS worker facilities related seismology.
"""

import collections
import datetime

from ramsis.sfm.worker.utils.extensions.misc import CoordinateMixin, DEFAULT_PROJ


class Catalog(collections.namedtuple('Catalog', ['date', 'events'])):
    """
    A seismic catalog in the context for RAMSIS workers.
    """
    __slots__ = ()

    def __new__(cls, date=datetime.datetime.utcnow(), events=[]):
        return super().__new__(cls, date=date, events=events)

    # __new__ ()

    @classmethod
    def from_dict(cls, catalog_dict,
                  argmap={'date': 'catalog_date',
                          'events': 'seismic_events'}):
        """
        Create a catalog from a :py:class:`dict`.

        :param dict catalog_dict: Seismic catalog
        :param dict argmap: Mapping for :py:class:`Catalog` / dictionary keys.
            If a key is missing it is assumed that keys are equal.

        :returns: Catalog instance
        :rtype: :py:class:`Catalog`
        """

        data = {}
        for f in cls._fields:
            try:
                data[f] = catalog_dict[argmap[f]]
            except KeyError:
                data[f] = catalog_dict[f]

        return cls(**data)

    # from_dict ()

    def transform(self, p2):
        for e in self.events:
            e.transform(p2)

    # transform ()

    def __iter__(self):
        for e in self.events:
            yield e

# class Catalog


class Event(CoordinateMixin):
    """
    Implementation of an seismic event.
    """

    def __init__(self, datetime, x, y, z, magnitude, proj=DEFAULT_PROJ):
        super().__init__(x, y, z, proj=proj)
        self._data = tuple([datetime, magnitude])

    @property
    def datetime(self):
        return self._data[0]

    @property
    def magnitude(self):
        return self._data[1]

# class Event


# ---- END OF <seismics.py> ----
