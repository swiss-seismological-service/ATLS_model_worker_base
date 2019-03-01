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

from collections import ChainMap

from osgeo import ogr, osr
from obspy import read_events

#from ramsis.worker.SaSS.core import sass
#from ramsis.worker.SaSS.core.reservoir import Reservoir

from ramsis.worker.utils import orm
from ramsis.worker.utils.model import (Model as _Model, ModelError,
                                       ModelResult)


class SaSSError(ModelError):
    """Base SaSS model error ({})."""

class ValidationError(SaSSError):
    """ValidationError ({})."""


# -----------------------------------------------------------------------------
class Model(_Model):
    """
    SaSS model implementation running the SaSS model code. The class wraps up
    model specifc code providing a unique interface.

    :param str reservoir_geometry: Reservoir geometry used by default.
        WKT format.
    :param dict model_parameters: Dictionary of model parameters used by
        default.
    """

    LOGGER = 'ramsis.worker.model_sass'

    NAME = 'SaSS'
    DESCRIPTION = 'Shapiro and Smoothed Seismicity'

    def __init__(self, **kwargs):
        super().__init__()

        self._default_reservoir = kwargs.get('reservoir')
        self._default_model_parameters = kwargs.get('model_parameters')

    # __init__ ()

    def _run(self, task_id, **kwargs):
        """
        :param kwargs: Model specific keyword value parameters.
        """
        def format_msg(msg):
            return '{!r}: {}'.format(self, msg)

        self.logger.debug(format_msg('Running model ...'))
        self.logger.debug(format_msg('Importing input parameters ...'))

        self.logger.debug(format_msg('Importing seismic catalog ...'))
        cat = read_events(
            io.BytesIO(kwargs['seismic_catalog']['quakeml'].encode('utf-8')))
        self.logger.debug(format_msg(
            'Received seismic catalog with {} event(s).'.format(len(cat))))

        self.logger.debug(format_msg('Importing scenario ...'))
        injection_plan = kwargs['scenario']
        self.logger.debug(format_msg(
            'Received injection plan with {} event(s).'.format(
                len(injection_plan['samples']))))

        self.logger.debug(format_msg(
            'Importing model specific configuration ...'))
        # XXX(damb): Use a single view of model parameters sent by the client
        # and default model parameters injected while starting the service
        model_config = ChainMap(kwargs.get('model_parameters', {}),
                                self._default_model_parameters)
        # XXX(damb): Default parameters are configured when starting the
        # worker.
        self.logger.debug(format_msg(
            'Received model configuration: {!r}'.format(model_config)))

        self.logger.debug(format_msg('Importing reservoir geometry ...'))

        # TODO(damb): Transform spatial data into local coordinate system
        # TODO TODO TODO

        reservoir_geom = kwargs['reservoir']['geom']
        try:
            _reservoir_geom = self._validate_geometry(reservoir_geom)
        except ValueError as err:
            raise ValidationError(err)

        try:
            proj = _reservoir_geom.GetSpatialReference().ExportToProj4()
            self.logger.warning(
                'Reservoir projection is ignored (PROJ4): {!r}. Assuming '
                'WGS84 (srid=4326). '.format(proj))
        except AttributeError as err:
            self.logger.debug(
                'No CRS information passed ({}). Assuming WGS84 '
                '(srid=4326).'.format(err))
            proj = ''

        # TODO TODO TODO
        # XXX(damb): We do not use CRS information for reservoir voxels.
        #reservoir = Reservoir.from_envelope(
        #    *_reservoir_geom.GetEnvelope3D(),
        #    dim_voxel=model_config['const_dim_voxel'])

        result = 73

        # XXX(damb): SaSS should return a reservoir independent from the
        # database (i.e.  orm.Reservoir) in order to have a fully modularized
        # model implementation independend of the worker ORM facilities.
        return ModelResult.ok(
            data={task_id: orm.Reservoir(geom=reservoir_geom,
                                         b_value=result)},
            warning=self.stderr if self.stderr else self.stdout)

    # _run ()

    @staticmethod
    def _validate_geometry(wkt_geom, srid=None):
        """
        Validate the reservoir geometry.

        :param str wkt_geom: Reservoir geometry description
        :param srid: Optional spatial reference identifier
        :type srid: int or None

        :returns: Geometry
        :rtype: dict

        :raises ValueError: If an invalid geometry was passed
        """

        def is_cuboid_xyz(geom):
            """
            Check if a a :code:`POLYHEDRALSURFACE` is cube-/cuboid-like in the
            xyz-plane

            :param geom: Geometry to be checked
            :type geom: :py:class:`osgeo.ogr.Geometry`

            :returns: :code:`True` if the geomentry is cube-/cuboid-like
            :rtype: bool
            """
            geom_env = geom.GetEnvelope3D()
            min_x = geom_env[0]
            max_x = geom_env[1]
            min_y = geom_env[2]
            max_y = geom_env[3]
            min_z = geom_env[4]
            max_z = geom_env[5]

            # define corner coordinates
            c0 = min_x, min_y, min_z
            c1 = min_x, max_y, min_z
            c2 = max_x, max_y, min_z
            c3 = max_x, min_y, min_z
            c4 = min_x, min_y, max_z
            c5 = min_x, max_y, max_z
            c6 = max_x, max_y, max_z
            c7 = max_x, min_y, max_z

            phsf = ogr.Geometry(ogr.wkbPolyhedralSurfaceZ)

            r0 = ogr.Geometry(ogr.wkbLinearRing)
            r0.AddPoint(*c0)
            r0.AddPoint(*c1)
            r0.AddPoint(*c2)
            r0.AddPoint(*c3)
            r0.AddPoint(*c0)
            p0 = ogr.Geometry(ogr.wkbPolygon)
            p0.AddGeometry(r0)
            phsf.AddGeometry(p0)

            r1 = ogr.Geometry(ogr.wkbLinearRing)
            r1.AddPoint(*c0)
            r1.AddPoint(*c1)
            r1.AddPoint(*c5)
            r1.AddPoint(*c4)
            r1.AddPoint(*c0)
            p1 = ogr.Geometry(ogr.wkbPolygon)
            p1.AddGeometry(r1)
            phsf.AddGeometry(p1)

            r2 = ogr.Geometry(ogr.wkbLinearRing)
            r2.AddPoint(*c0)
            r2.AddPoint(*c3)
            r2.AddPoint(*c7)
            r2.AddPoint(*c4)
            r2.AddPoint(*c0)
            p2 = ogr.Geometry(ogr.wkbPolygon)
            p2.AddGeometry(r2)
            phsf.AddGeometry(p2)

            r3 = ogr.Geometry(ogr.wkbLinearRing)
            r3.AddPoint(*c6)
            r3.AddPoint(*c7)
            r3.AddPoint(*c4)
            r3.AddPoint(*c5)
            r3.AddPoint(*c6)
            p3 = ogr.Geometry(ogr.wkbPolygon)
            p3.AddGeometry(r3)
            phsf.AddGeometry(p3)

            r4 = ogr.Geometry(ogr.wkbLinearRing)
            r4.AddPoint(*c6)
            r4.AddPoint(*c7)
            r4.AddPoint(*c3)
            r4.AddPoint(*c2)
            r4.AddPoint(*c6)
            p4 = ogr.Geometry(ogr.wkbPolygon)
            p4.AddGeometry(r4)
            phsf.AddGeometry(p4)

            r5 = ogr.Geometry(ogr.wkbLinearRing)
            r5.AddPoint(*c6)
            r5.AddPoint(*c2)
            r5.AddPoint(*c1)
            r5.AddPoint(*c5)
            r5.AddPoint(*c6)
            p5 = ogr.Geometry(ogr.wkbPolygon)
            p5.AddGeometry(r5)
            phsf.AddGeometry(p5)

            return phsf.Equals(geom)

        # is_cuboid_xyz ()

        try:
            geom = ogr.CreateGeometryFromWkt(wkt_geom)
        except Exception as err:
            raise ValueError(err)

        if srid is not None:
            try:
                spatial_ref = osr.SpatialReference()
                spatial_ref.ImportFromEPSG(srid)

                geom.AssignSpatialReference(spatial_ref)
            except Exception as err:
                raise ValueError(
                    'While assigning SRID parameter: {}'.format(err))

        geom.CloseRings()

        if (geom.GetGeometryName() != 'POLYHEDRALSURFACE' or
            geom.GetGeometryCount() != 6 or not
                is_cuboid_xyz(geom)):
            raise ValueError(
                'Invalid geometry ({!r}).'.format(wkt_geom))

        return geom

    # _validate_geometry ()

# class Model

# ---- END OF <model.py> ----
