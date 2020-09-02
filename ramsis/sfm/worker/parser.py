# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
Parsing facilities for worker webservices.
"""

import base64
import re
import datetime
from marshmallow import (fields, pre_load,
                         utils, post_load)
import dateutil.parser
from webargs.flaskparser import abort
from webargs.flaskparser import parser as _parser
from functools import partial

from ramsis.sfm.worker.utils import (StatusCode, SchemaBase,
                                     Positive,
                                     Percentage,
                                     validate_ph,
                                     validate_longitude,
                                     validate_latitude)


Latitude = partial(fields.Float, validate=validate_latitude)
RequiredLatitude = partial(Latitude, required=True)
Longitude = partial(fields.Float, validate=validate_longitude)
RequiredLongitude = partial(Longitude, required=True)
FluidPh = partial(fields.Float, validate=validate_ph)


# from marshmallow (originally from Django)
_iso8601_re = re.compile(
    r'(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})'
    r'[T ](?P<hour>\d{1,2}):(?P<minute>\d{1,2})'
    r'(?::(?P<second>\d{1,2})(?:\.(?P<microsecond>\d{1,6})\d{0,6})?)?'
    # tzinfo must not be available
    r'(?P<tzinfo>(?!\Z|[+-]\d{2}(?::?\d{2})?))?$'
)


def datetime_to_isoformat(dt, localtime=False, *args, **kwargs):
    """
    Convert a :py:class:`datetime.datetime` object to a ISO8601 conform string.
    :param datetime.datetime dt: Datetime object to be converted
    :param bool localtime: The parameter is ignored
    :returns: ISO8601 conform datetime string
    :rtype: str
    """
    # ignores localtime parameter
    return dt.isoformat(*args, **kwargs)


def string_to_datetime(datestring, use_dateutil=True):
    """
    Parse a datestring from a string specified by the FDSNWS datetime
    specification.
    :param str datestring: String to be parsed
    :param bool use_dateutil: Make use of the :code:`dateutil` package if set
        to :code:`True`
    :returns: Datetime
    :rtype: :py:class:`datetime.datetime`
    See: http://www.fdsn.org/webservices/FDSN-WS-Specifications-1.1.pdf
    """
    IGNORE_TZ = True

    if len(datestring) == 10:
        # only YYYY-mm-dd is defined
        return datetime.datetime.combine(utils.from_iso_date(datestring,
                                         use_dateutil), datetime.time())
    else:
        if not _iso8601_re.match(datestring):
            raise ValueError('Not a valid ISO8601-formatted string.')
        return dateutil.parser.parse(datestring, ignoretz=IGNORE_TZ)


class UTCDateTime(fields.DateTime):
    """
    The class extends marshmallow standard DateTime with a FDSNWS *datetime*
    format.
    The FDSNWS *datetime* format is described in the `FDSN Web Service
    Specifications
    <http://www.fdsn.org/webservices/FDSN-WS-Specifications-1.1.pdf>`_.
    """

    SERIALIZATION_FUNCS = fields.DateTime.SERIALIZATION_FUNCS.copy()

    DESERIALIZATION_FUNCS = fields.DateTime.DESERIALIZATION_FUNCS.copy()

    SERIALIZATION_FUNCS['utc_isoformat'] = datetime_to_isoformat
    DESERIALIZATION_FUNCS['utc_isoformat'] = string_to_datetime


class TupleField(fields.Field):

    def __init__(self, entries, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._entries = entries

    def _deserialize(self, value, attr=None, data=None):
        return tuple(
            field._deserialize(val, attr, data) for field, val in
            zip(self._entries, value))


class SeismicCatalogSchema(SchemaBase):
    """
    Schema representation of a seismic catalog.
    """
    quakeml = fields.String(required=True)

    @pre_load
    def b64decode(self, data, **kwargs):
        """
        Decode the base64 encoded catalog. Return a `QuakeML
        <https://quake.ethz.ch/quakeml/QuakeML>`_ string.
        """
        if 'quakeml' in data:
            data['quakeml'] = base64.b64decode(
                data['quakeml']).decode('utf-8')

        return data


class HydraulicSampleSchema(SchemaBase):
    """
    Schema representation for an hydraulic sample.
    """
    fluidcomposition = fields.String()

    datetime_value = UTCDateTime("utc_isoformat", required=True)
    datetime_uncertainty = Positive()
    datetime_loweruncertainty = Positive()
    datetime_upperuncertainty = Positive()
    datetime_confidencelevel = Percentage()

    toptemperature_value = Positive()
    toptemperature_uncertainty = Positive()
    toptemperature_loweruncertainty = Positive()
    toptemperature_upperuncertainty = Positive()
    toptemperature_confidencelevel = Percentage()

    bottomtemperature_value = Positive()
    bottomtemperature_uncertainty = Positive()
    bottomtemperature_loweruncertainty = Positive()
    bottomtemperature_upperuncertainty = Positive()
    bottomtemperature_confidencelevel = Percentage()

    topflow_value = fields.Float()
    topflow_uncertainty = Positive()
    topflow_loweruncertainty = Positive()
    topflow_upperuncertainty = Positive()
    topflow_confidencelevel = Percentage()

    bottomflow_value = fields.Float()
    bottomflow_uncertainty = Positive()
    bottomflow_loweruncertainty = Positive()
    bottomflow_upperuncertainty = Positive()
    bottomflow_confidencelevel = Percentage()

    toppressure_value = Positive()
    toppressure_uncertainty = Positive()
    toppressure_loweruncertainty = Positive()
    toppressure_upperuncertainty = Positive()
    toppressure_confidencelevel = Percentage()

    bottompressure_value = Positive()
    bottompressure_uncertainty = Positive()
    bottompressure_loweruncertainty = Positive()
    bottompressure_upperuncertainty = Positive()
    bottompressure_confidencelevel = Percentage()

    fluiddensity_value = Positive()
    fluiddensity_uncertainty = Positive()
    fluiddensity_loweruncertainty = Positive()
    fluiddensity_upperuncertainty = Positive()
    fluiddensity_confidencelevel = Percentage()

    fluidviscosity_value = Positive()
    fluidviscosity_uncertainty = Positive()
    fluidviscosity_loweruncertainty = Positive()
    fluidviscosity_upperuncertainty = Positive()
    fluidviscosity_confidencelevel = Percentage()

    fluidph_value = FluidPh()
    fluidph_uncertainty = Positive()
    fluidph_loweruncertainty = Positive()
    fluidph_upperuncertainty = Positive()
    fluidph_confidencelevel = Percentage()


class BoreholeSectionSchema(SchemaBase):
    """
    Schema representation of a borehole section.
    """
    starttime = UTCDateTime('utc_isoformat')
    endtime = UTCDateTime('utc_isoformat')
    toplongitude_value = Longitude()
    toplongitude_uncertainty = Positive()
    toplongitude_loweruncertainty = Positive()
    toplongitude_upperuncertainty = Positive()
    toplongitude_confidencelevel = Percentage()

    bottomlongitude_value = Longitude()
    bottomlongitude_uncertainty = Positive()
    bottomlongitude_loweruncertainty = Positive()
    bottomlongitude_upperuncertainty = Positive()
    bottomlongitude_confidencelevel = Percentage()

    toplatitude_value = Latitude()
    toplatitude_uncertainty = Positive()
    toplatitude_loweruncertainty = Positive()
    toplatitude_upperuncertainty = Positive()
    toplatitude_confidencelevel = Percentage()

    bottomlatitude_value = Latitude()
    bottomlatitude_uncertainty = Positive()
    bottomlatitude_loweruncertainty = Positive()
    bottomlatitude_upperuncertainty = Positive()
    bottomlatitude_confidencelevel = Percentage()

    topdepth_value = Positive()
    topdepth_uncertainty = Positive()
    topdepth_loweruncertainty = Positive()
    topdepth_upperuncertainty = Positive()
    topdepth_confidencelevel = Percentage()

    bottomdepth_value = Positive()
    bottomdepth_uncertainty = Positive()
    bottomdepth_loweruncertainty = Positive()
    bottomdepth_upperuncertainty = Positive()
    bottomdepth_confidencelevel = Percentage()

    holediameter_value = Positive()
    holediameter_uncertainty = Positive()
    holediameter_loweruncertainty = Positive()
    holediameter_upperuncertainty = Positive()
    holediameter_confidencelevel = Percentage()

    casingdiameter_value = Positive()
    casingdiameter_uncertainty = Positive()
    casingdiameter_loweruncertainty = Positive()
    casingdiameter_upperuncertainty = Positive()
    casingdiameter_confidencelevel = Percentage()

    topclosed = fields.Boolean()
    bottomclosed = fields.Boolean()
    sectiontype = fields.String()
    casingtype = fields.String()
    description = fields.String()

    publicid = fields.String()

    hydraulics = fields.Nested(HydraulicSampleSchema, many=True, required=True)


class BoreholeSchema(SchemaBase):
    """
    Schema representation for a borehole.
    """
    # XXX(damb): publicid is currently not required since we exclusively
    # support a single borehole.
    publicid = fields.String()

    bedrockdepth_value = Positive()
    bedrockdepth_uncertainty = Positive()
    bedrockdepth_loweruncertainty = Positive()
    bedrockdepth_upperuncertainty = Positive()
    bedrockdepth_confidencelevel = Percentage()

    altitude_value = fields.Float()
    altitude_uncertainty = Positive()
    altitude_loweruncertainty = Positive()
    altitude_upperuncertainty = Positive()
    altitude_confidencelevel = Percentage()

    sections = fields.Nested(BoreholeSectionSchema, many=True, required=True)


class ScenarioSchema(SchemaBase):
    """
    Schema representation for a scenario to be forecasted.
    """
    # XXX(damb): Borehole scenario for both the related geometry and the
    # injection plan.
    well = fields.Nested(BoreholeSchema, required=True)


class ReservoirSchema(SchemaBase):
    """
    Schema representation of a reservoir to be forecasted.
    """
    x = fields.List(fields.Float(), required=True)
    y = fields.List(fields.Float(), required=True)
    z = fields.List(fields.Float(), required=True)

    @pre_load
    def validate_geom(self, data, **kwargs):
        assert set(['x', 'y', 'z']) <= set(data.keys())
        for dim in ['x', 'y', 'z']:
            val_list = data[dim]
            assert isinstance(val_list, list), ("Dimensional list length "
                                                "must equal or exceed 2")
            # Check that the values in each list are strictly increasing
            # Same numbers are not allowed as that would create zero-width
            # subgeometries.
            assert all(x < y for x, y in zip(val_list, val_list[1:]))
            assert len(val_list) >= 2
        return data


class GeomSchema(SchemaBase):
    """
    Schema representing the geometry of a reservoir.
    """
    geom = fields.Nested(ReservoirSchema)


class ModelParameterSchemaBase(SchemaBase):
    """
    Model parameter schema base class.
    """
    # XXX(damb): Forecast specific parameters
    datetime_start = UTCDateTime('utc_isoformat', required=True)
    datetime_end = UTCDateTime('utc_isoformat', required=True)
    epoch_duration = fields.Float()


class ReferencePointSchema(SchemaBase):
    x = fields.Float(required=True)
    y = fields.Float(required=True)


def create_sfm_worker_imessage_schema(
        model_parameters_schema=ModelParameterSchemaBase):
    """
    Factory function for a SFM worker :code:`runs/` input message schema.

    :param model_parameters_schema: Schema for model parameters.
    :type model_parameters_schema: :py:class:`marshmallow.Schema`
    """

    class _SFMWorkerRunsAttributesSchema(SchemaBase):
        """
        Schema implementation for deserializing attributes seismicity
        forecast model worker implementations.

        .. note::

            With the current protocol version only a single well is supported.
        """
        spatialreference = fields.String(required=True)
        referencepoint = fields.Nested(ReferencePointSchema)
        seismic_catalog = fields.Nested(SeismicCatalogSchema, required=True)
        # NOTE(damb): A well comes along with its hydraulics.
        well = fields.Nested(BoreholeSchema, required=True)
        scenario = fields.Nested(ScenarioSchema, required=True)
        reservoir = fields.Nested(GeomSchema, required=True)
        model_parameters = fields.Nested(model_parameters_schema,
                                         required=True)

        @post_load
        def pre_load(self, data, **kwargs):
            return data

    class _SFMWorkerRunsSchema(SchemaBase):
        type = fields.Str(missing='runs')
        attributes = fields.Nested(_SFMWorkerRunsAttributesSchema)

    class _SFMWorkerIMessageSchema(SchemaBase):
        """
        Schema implementation for serializing input messages for seismicity
        forecast model worker implementations.
        """
        data = fields.Nested(_SFMWorkerRunsSchema)

    return _SFMWorkerIMessageSchema


SFMWorkerIMessageSchema = create_sfm_worker_imessage_schema()


@_parser.error_handler
def handle_request_parsing_error(err, req, schema, error_status_code,
                                 error_headers):
    """
    Webargs error handler that uses Flask-RESTful's abort function
    to return a JSON error response to the client.
    """
    abort(StatusCode.UnprocessableEntity.value,
          errors=err.messages)


parser = _parser
