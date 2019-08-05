# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
Parsing facilities for worker webservices.
"""

import base64

from marshmallow import (fields, pre_load, post_load, validates_schema,
                         ValidationError)
from webargs.flaskparser import abort
from webargs.flaskparser import parser as _parser

from ramsis.sfm.worker.utils import (StatusCode, SchemaBase,
                                     QuakeMLQuantitySchemaBase,
                                     QuakeMLRealQuantitySchema,
                                     validate_positive,
                                     validate_ph,
                                     validate_longitude,
                                     validate_latitude)



class TupleField(fields.Field):

    def __init__(self, entries, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._entries = entries

    def _deserialize(self, value, attr=None, data=None):
        return tuple(
            field._deserialize(val, attr, data) for field, val in
            zip(self._entries, value))

class QuakeMLTimeQuantitySchema(QuakeMLQuantitySchemaBase):
    """
    Schema representation of a `QuakeML <https://quake.ethz.ch/quakeml/>`_
    TimeQuantity type.
    """
    value = fields.DateTime(format='iso')


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
    datetime = fields.Nested(QuakeMLTimeQuantitySchema,
                             required=True)
    bottomtemperature = fields.Nested(
        QuakeMLRealQuantitySchema(validate=validate_positive))
    bottomflow = fields.Nested(QuakeMLRealQuantitySchema())
    bottompressure = fields.Nested(QuakeMLRealQuantitySchema())
    toptemperature = fields.Nested(
        QuakeMLRealQuantitySchema(validate=validate_positive))
    topflow = fields.Nested(QuakeMLRealQuantitySchema())
    toppressure = fields.Nested(QuakeMLRealQuantitySchema())
    fluiddensity = fields.Nested(
        QuakeMLRealQuantitySchema(validate=validate_positive))
    fluidviscosity = fields.Nested(
        QuakeMLRealQuantitySchema(validate=validate_positive))
    fluidph = fields.Nested(
        QuakeMLRealQuantitySchema(validate=validate_ph))
    fluidcomposition = fields.String()


class BoreholeSectionSchema(SchemaBase):
    """
    Schema representation of a borehole section.
    """
    starttime = fields.DateTime(format='iso')
    endtime = fields.DateTime(format='iso')

    toplongitude = fields.Nested(
        QuakeMLRealQuantitySchema(validate=validate_longitude),
        required=True)
    toplatitude = fields.Nested(
        QuakeMLRealQuantitySchema(validate=validate_latitude),
        required=True)
    topdepth = fields.Nested(
        QuakeMLRealQuantitySchema(validate=validate_positive),
        required=True)
    bottomlongitude = fields.Nested(
        QuakeMLRealQuantitySchema(validate=validate_longitude),
        required=True)
    bottomlatitude = fields.Nested(
        QuakeMLRealQuantitySchema(validate=validate_latitude),
        required=True)
    bottomdepth = fields.Nested(
        QuakeMLRealQuantitySchema(validate=validate_positive),
        required=True)
    holediameter = fields.Nested(
        QuakeMLRealQuantitySchema(validate=validate_positive))
    casingdiameter = fields.Nested(
        QuakeMLRealQuantitySchema(validate=validate_positive))

    topclosed = fields.Boolean()
    bottomclosed = fields.Boolean()
    sectiontype = fields.String()
    casingtype = fields.String()
    description = fields.String()

    publicid = fields.String()

    hydraulics = fields.Nested(HydraulicSampleSchema, many=True)


class BoreholeSchema(SchemaBase):
    """
    Schema representation for a borehole.
    """
    # XXX(damb): publicid is currently not required since we exclusively
    # support a single borehole.
    publicid = fields.String()
    bedrockdepth = fields.Nested(
        QuakeMLRealQuantitySchema(validate=validate_positive))

    sections = fields.Nested(BoreholeSectionSchema, many=True, required=True)

    @validates_schema
    def validate_sections(self, data, **kwargs):
        if len(data['sections']) != 1:
            raise ValidationError(
                'InjectionWells are required to have a single section.')


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
    # XXX(damb): WKT/WKB
    geom = fields.String(required=True)


class ModelParameterSchemaBase(SchemaBase):
    """
    Model parameter schema base class.
    """


    # dim-x, dim-y, dim-z in meters
    voxel_dimensions_m = TupleField(
        [fields.Float(required=True), fields.Float(required=True),
         fields.Float(required=True)])
    local_srs = fields.String()

    # ----
    #XXX(damb): Forecast specific parameters
    fc_datetime_start = fields.DateTime(format='iso', required=True)
    fc_datetime_end = fields.DateTime(format='iso', required=True)
    fc_increment_seconds = fields.Float()
    fc_threshold_magnitude = fields.Float()


    # ----
    #XXX(damb): Training specific parameters
    # Leave blank, as the default config within em1_model will check the
    # hydraulic input and form training period on this
    training_seconds = fields.Float()
    end_training = fields.DateTime()
    training_events_threshold = fields.Integer()

    # duration in seconds
    bin_duration = fields.Float()



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
        seismic_catalog = fields.Nested(SeismicCatalogSchema, required=True)
        # NOTE(damb): A well comes along with its hydraulics.
        well = fields.Nested(BoreholeSchema, required=True)
        scenario = fields.Nested(ScenarioSchema, required=True)
        reservoir = fields.Nested(ReservoirSchema, required=True)
        model_parameters = fields.Nested(model_parameters_schema,
                                         required=True)

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


SFMWorkerIMessageSchema = create_sfm_worker_imessage_schema(model_parameters_schema=ModelParameterSchemaBase)


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
