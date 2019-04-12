# This is <reservoir.py>
# ----------------------------------------------------------------------------
#
# Copyright (c) 2018 by Daniel Armbruster (SED, ETHZ)
#
#
# REVISIONS and CHANGES
# 2018/10/22    V1.0   Daniel Armbruster
#
# ============================================================================
"""
*SaSS* model reservoir facilities.
"""

import collections

import numpy as np

from ramsis.worker.SaSS.core import DEFAULT_DIM_VOXEL
from ramsis.worker.SaSS.core.utils import SaSSCoreError
from ramsis.worker.utils.extensions.misc import CoordinateMixin as Coordinate


# ----------------------------------------------------------------------------
class Reservoir(collections.namedtuple('Reservoir',
                                       ['xx', 'yy', 'zz', 'proj'])):
    """
    Implementation of a cube-/cuboid-like *SaSS*-compatible reservoir. The
    implementation is based on :py:function:`numpy.meshgrid`
    """

    class ReservoirError(SaSSCoreError):
        """Base reservoir error ({})."""

    class MissingProjection(ReservoirError):
        """Missing projection property."""

    def transform(self, p2_proj):

        if not self.proj:
            raise self.MissingProjection()

        # TODO TODO TODO
        raise NotImplementedError

    # transform ()

    @classmethod
    def from_envelope(cls, x_min, x_max, y_min, y_max, z_min, z_max,
                      dim_voxel=DEFAULT_DIM_VOXEL):
        """
        Returns a :py:class:`SaSS` model compatible reservoir given by a
        :py:class:`osgeo.ogr.Geometry` 3D envelope.

        :param float x_min: Lower reservoir x-boundery in meters
        :param float x_max: Upper reservoir x-boundery in meters
        :param float y_min: Lower reservoir y-boundery in meters
        :param float y_max: Upper reservoir y-boundery in meters
        :param float z_min: Lower reservoir z-boundery in meters
        :param float z_max: Upper reservoir z-boundery in meters
        :param tuple dim_voxel: Voxel dimensions :code:`(x,y,z)` in meters used
            for the spatial binning.

        :returns: Spatially gridded reservoir using center coordinates
        :rtype: :py:class:`Reservoir`

        .. note::

            Passing CRS information currently is not supported.
        """
        x = np.linspace(x_min, x_max, abs(x_max-x_min)/dim_voxel[0]+1)
        y = np.linspace(y_min, y_max, abs(y_max-y_min)/dim_voxel[1]+1)
        z = np.linspace(z_min, z_max, abs(z_max-z_min)/dim_voxel[2]+1)
        xx, yy, zz = np.meshgrid((x[1:] + x[:-1]) / 2,
                                 (y[1:] + y[:-1]) / 2,
                                 (z[1:] + z[:-1]) / 2, indexing='ij')

        return cls(xx=xx, yy=yy, zz=zz, proj='')

    # from_envelope ()

    def __iter__(self):
        nx, ny, nz = self.xx.shape
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    yield Coordinate(x=self.xx[i, j, k], y=self.yy[i, j, k],
                                     z=self.zz[i, j, k], proj=self.proj)

    # __iter__ ()

# class Reservoir


# ---- END OF <reservoir.py> ----
