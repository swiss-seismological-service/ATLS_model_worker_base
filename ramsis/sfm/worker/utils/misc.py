# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
Extensions for miscellaneous entities.
"""
from copy import deepcopy
import warnings
from osgeo import ogr, osr
from pyproj import Transformer

from ramsis.utils.error import ErrorWithTraceback
from ramsis.sfm.worker.orm import Reservoir


# DEFAULT_PROJ = '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs'
DEFAULT_PROJ = ''


def transform(x, y, source_proj, target_proj=4326):
    """
    Transform coordinates from a coordinate system defined by :code:`p1_proj4`
    to the coordinate system defined by :code:`p2_proj4`.

    :param x: X-value of coordinate to be transformed
    :param y: Y-value of coordinate to be transformed
    :param z: Z-value of coordinate to be transformed
    :param str target_proj: `PROJ.4 <https://proj4.org/>`_ project string
        defining the target coordinate system. When e.g. transforming into a
        local *NED* coordinate system a string such as :code:`+proj=etmerc
        +ellps=WSG84 +lon_0=<observer_lon> +lat_0=<observer_lat> +x_0=0 +y_0=0
        +z_0=<observer_alt> +k_0=1 +units=m +axis=ned` might give a good
        approximation.
    :param str source_proj: `PROJ.4 <https://proj4.org/>`_ project string
        describing the source coordinate system
    """
    transformer = Transformer.from_proj(source_proj, target_proj)

    lat, lon = transformer.transform(x, y)
    return lon, lat


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


def single_reservoir_result(geom, samples):
    """
    Function to create a single reservoir with results when
    a single result set should be used for the entire geometry.
    """
    reservoir = Reservoir(z_min=min(geom["z"]),
                          z_max=max(geom["z"]),
                          y_min=min(geom["y"]),
                          y_max=max(geom["y"]),
                          x_min=min(geom["x"]),
                          x_max=max(geom["x"]),
                          samples=deepcopy(samples))
    return reservoir


def subgeoms_for_single_result(geom, samples):
    """
    Function to create a reservoir with sub geometries when
    a single result set should be used for the entire geometry.
    """
    def tuples_for_list(d_list):
        return [(d_list[i], d_list[i + 1]) for i in range(len(d_list) - 1)]
    subgeoms = []

    for x_tup in tuples_for_list(geom['x']):
        x_min = x_tup[0]
        x_max = x_tup[1]
        for y_tup in tuples_for_list(geom['y']):
            y_min = y_tup[0]
            y_max = y_tup[1]
            for z_tup in tuples_for_list(geom['z']):
                z_min = z_tup[0]
                z_max = z_tup[1]
                subgeoms.append(Reservoir(x_min=x_min,
                                          x_max=x_max,
                                          y_min=y_min,
                                          y_max=y_max,
                                          z_min=z_min,
                                          z_max=z_max,
                                samples=deepcopy(samples)))
    return Reservoir(subgeometries=subgeoms)
