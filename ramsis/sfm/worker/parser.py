# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
Parsing facilities for worker webservices.
"""

import base64
import functools

from marshmallow import (Schema, fields, pre_load, validate, validates_schema,
                         ValidationError)
from webargs.flaskparser import abort
from webargs.flaskparser import parser as _parser

from ramsis.sfm.worker.utils import StatusCode


def validate_positive(d):
    return d >= 0


validate_percentage = validate.Range(min=0, max=100)
validate_longitude = validate.Range(min=-180., max=180.)
validate_latitude = validate.Range(min=-90., max=90)
validate_ph = validate.Range(min=0, max=14)

Positive = functools.partial(fields.Float, validate=validate_positive)
Percentage = functools.partial(fields.Float, validate=validate_percentage)


class SchemaBase(Schema):

    class Meta:
        strict = True


class QuakeMLQuantitySchemaBase(SchemaBase):
    uncertainty = Positive()
    loweruncertainty = Positive()
    upperuncertainty = Positive()
    confidencelevel = Percentage()


class QuakeMLTimeQuantitySchema(QuakeMLQuantitySchemaBase):
    """
    Schema representation of a `QuakeML <https://quake.ethz.ch/quakeml/>`_
    TimeQuantity type.
    """
    value = fields.DateTime(format='iso')


def QuakeMLRealQuantitySchema(validate=None):
    """
    Factory function for a `QuakeML <https://quake.ethz.ch/quakeml/>`_
    RealQuantity type.
    """

    class _QuakeMLRealQuantitySchema(QuakeMLQuantitySchemaBase):
        value = fields.Float(validate=validate)

    return _QuakeMLRealQuantitySchema


class SeismicCatalogSchema(SchemaBase):
    """
    Schema representation of a seismic catalog.
    """
    quakeml = fields.String(required=True)

    @pre_load
    def b64decode(self, data):
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
    def validate_sections(self, data):
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


class SFMWorkerIMessageSchema(SchemaBase):
    """
    Schema implementation for serializing input messages for seismicity
    forecast model worker implementations.

    .. note::

        With the current protocol version only a single well is supported.
    """
    seismic_catalog = fields.Nested(SeismicCatalogSchema, required=True)
    # XXX(damb): Implicit definition of an injection well in order to allow
    # serialization by means of the appropriate RT-RAMSIS borehole serializer.
    # Note, that a well comes along with its hydraulics.
    well = fields.Nested(BoreholeSchema, required=True)
    scenario = fields.Nested(ScenarioSchema, required=True)
    reservoir = fields.Nested(ReservoirSchema, required=True)
    # XXX(damb): model_parameters are optional
    model_parameters = fields.Dict(keys=fields.Str())


# Flask-RESTful error handler
@_parser.error_handler
def handle_request_parsing_error(err, req, schema):
    """
    Webargs error handler that uses Flask-RESTful's abort function
    to return a JSON error response to the client.
    """
    abort(StatusCode.UnprocessableEntity.value,
          errors=err.messages)


parser = _parser
