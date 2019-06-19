# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
Extensions for miscellaneous entities.
"""

import warnings

from ramsis.utils.error import ErrorWithTraceback

from osgeo import ogr, osr
from pyproj import Proj, transform as _transform

# DEFAULT_PROJ = '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs'
DEFAULT_PROJ = ''


def transform(x, y, z, p1_proj4, p2_proj4):
    """
    Transform coordinates from a coordinate system defined by :code:`p1_proj4`
    to the coordinate system defined by :code:`p2_proj4`.

    :param x: X-value of coordinate to be transformed
    :param y: Y-value of coordinate to be transformed
    :param z: Z-value of coordinate to be transformed
    :param str p2_proj4: `PROJ.4 <https://proj4.org/>`_ project string
        defining the target coordinate system. When e.g. transforming into a
        local *NED* coordinate system a string such as :code:`+proj=etmerc
        +ellps=WSG84 +lon_0=<observer_lon> +lat_0=<observer_lat> +x_0=0 +y_0=0
        +z_0=<observer_alt> +k_0=1 +units=m +axis=ned` might give a good
        approximation.
    :param str p1_proj4: `PROJ.4 <https://proj4.org/>`_ project string
        describing the source coordinate system

    :code:`x`,:code:`y` and :code:`z` can be `numpy <http://www.numpy.org/>`_
    or regular python arrays, python lists/tuples or scalars. Arrays are
    fastest.
    """
    p1 = Proj(p1_proj4)
    p2 = Proj(p2_proj4)

    return _transform(p1, p2, x, y, z)


# -----------------------------------------------------------------------------
class CoordinateMixin(object):

    class CoordinateError(ErrorWithTraceback):
        """Base coordinate error ({})."""

    class MissingProjection(CoordinateError):
        """Missing projection information."""

    def __init__(self, **kwargs):
        self._x = kwargs['x']
        self._y = kwargs['y']
        self._z = kwargs.get('z')

        self._proj = kwargs.get('proj', DEFAULT_PROJ)

    def transform(self, p2):
        if not self._proj:
            raise self.MissingProjection()

        if self._z is None:
            self._x, self._y = transform(
                self._x, self._y, p1_proj4=self._proj, p2_proj4=p2)
            return

        self._x, self._y, self._z = transform(
            self._x, self._y, self._z, p1_proj4=self._proj, p2_proj4=p2)

    @classmethod
    def from_wkt(cls, wkt, proj=DEFAULT_PROJ):
        """
        Create a coordinate instance from a :code:`WKT` representation.

        :param str wkt: :code:`WKT` describing the coordinate
        :param str proj: `PROJ.4 <https://proj4.org/>`_ project string

        :returns: Class instance of :py:class:`CoordinateMixin`

        :raises ValueError: For invalid :code:`ẀKT` elements
        """

        try:
            p = ogr.CreateGeometryFromWkt(wkt)

            if p.GetGeometryName() != 'POINT Z':
                raise ValueError(
                    'Invalid geometry: {!r}.'.format(p.GetGeometryName()))
            if proj:
                spatial_ref = osr.SpatialReference()
                proj = spatial_ref.ImportFromProj4(proj).ExportToProj4()

            return cls(x=p.GetX(), y=p.GetY(), z=p.GetZ(), proj=proj)

        except Exception as err:
            raise ValueError(err)

    def wkt(self):
        if self._proj:
            warnings.warn(
                'Projection currently not taken into consideration.')
        # TODO(damb): Take the projection into consideration.
        return 'POINT Z (%f %f %f)' % self._x, self._y, self._z

    def __repr__(self):
        return '<CoordinateMixin(x=%s, y=%s, z=%s)>' % (
            self._x, self._y, self._z)
