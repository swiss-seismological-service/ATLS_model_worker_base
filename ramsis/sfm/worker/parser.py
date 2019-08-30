# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
Parsing facilities for worker webservices.
"""

import base64

from marshmallow import (fields, pre_load, post_load, validate, validates_schema,
                         ValidationError)

from webargs.flaskparser import abort
from webargs.flaskparser import parser as _parser
from functools import partial

from ramsis.sfm.worker.utils import (StatusCode, SchemaBase,
                                     Positive,
                                     Percentage,
                                     validate_positive,
                                     validate_ph,
                                     validate_longitude,
                                     validate_latitude)


Datetime = partial(fields.DateTime, format='%Y-%m-%dT%H:%M:%S.%f')
DatetimeRequired = partial(Datetime, required=True)
Latitude = partial(fields.Float, validate=validate_latitude)
RequiredLatitude = partial(Latitude, required=True)
Longitude = partial(fields.Float, validate=validate_longitude)
RequiredLongitude = partial(Longitude, required=True)
FluidPh = partial(fields.Float, validate=validate_ph)


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

    datetime_value = DatetimeRequired()
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
    starttime = Datetime()
    endtime = Datetime()
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
    #XXX(damb): Forecast specific parameters
    datetime_start = DatetimeRequired()
    datetime_end = DatetimeRequired()
    epoch_duration = fields.Float()
    threshold_magnitude = fields.Float()

    # ----
    #XXX(damb): Training specific parameters
    # Leave blank, as the default config within em1_model will check the
    # hydraulic input and form training period on this
    training_epoch_duration = fields.Float()
    end_training = Datetime()
    training_events_threshold = fields.Integer()


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
