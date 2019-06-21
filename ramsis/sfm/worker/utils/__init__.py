# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
General purpose ramsis.sfm.workers utilities
"""
import argparse
import enum
import functools
import logging
import pkg_resources

from marshmallow import Schema, fields, post_dump, validate


def get_version(namespace_pkg_name=None):
    """
    fetch version string

    :param str namespace_pkg_name: distribution name of the namespace package
    :returns: version string
    :rtype: str
    """
    try:
        # distributed as namespace package
        if namespace_pkg_name:
            return pkg_resources.get_distribution(namespace_pkg_name).version
        raise
    except Exception:
        return pkg_resources.get_distribution("ramsis.sfm.worker").version


def escape_newline(s):
    """
    Escape newline characters.

    :param str s: String to be processed.
    """
    return s.replace('\n', '\\n').replace('\r', '\\r')


def url(url):
    """
    check if SQLite URL is absolute.
    """
    if (url.startswith('sqlite:') and not
            (url.startswith('////', 7) or url.startswith('///C:', 7))):
        raise argparse.ArgumentTypeError('SQLite URL must be absolute.')
    return url


class ContextLoggerAdapter(logging.LoggerAdapter):
    """
    Adapter expecting the passed in dict-like object to have a 'ctx' key, whose
    value in brackets is prepended to the log message.
    """
    def process(self, msg, kwargs):
        return '[%s] %s' % (self.extra['ctx'], msg), kwargs


# -----------------------------------------------------------------------------
class StatusCode(enum.Enum):
    """
    SFM-Worker status code enum.
    """
    # codes related to worker states
    TaskAccepted = 202
    TaskProcessing = 423
    TaskError = 418
    TaskCompleted = 200
    TaskNotAvailable = 204
    # codes related to worker resource
    HTTPMethodNotAllowed = 405
    UnprocessableEntity = 422
    WorkerError = 500


def validate_positive(d):
    return d >= 0


validate_percentage = validate.Range(min=0, max=100)
validate_longitude = validate.Range(min=-180., max=180.)
validate_latitude = validate.Range(min=-90., max=90)
validate_ph = validate.Range(min=0, max=14)

Positive = functools.partial(fields.Float, validate=validate_positive)
Percentage = functools.partial(fields.Float, validate=validate_percentage)


class SchemaBase(Schema):

    @classmethod
    def _clear_missing(cls, data):
        retval = data.copy()
        for key in filter(lambda key: data[key] is None, data):
            del retval[key]
        return retval

    class Meta:
        strict = True


class QuakeMLQuantitySchemaBase(SchemaBase):
    uncertainty = Positive()
    loweruncertainty = Positive()
    upperuncertainty = Positive()
    confidencelevel = Percentage()


def QuakeMLRealQuantitySchema(validate=None):
    """
    Factory function for a `QuakeML <https://quake.ethz.ch/quakeml/>`_
    RealQuantity type.
    """

    class _QuakeMLRealQuantitySchema(QuakeMLQuantitySchemaBase):
        value = fields.Float(validate=validate)

        @post_dump
        def clear_missing(self, data):
            return self._clear_missing(data)

    return _QuakeMLRealQuantitySchema


class ModelResultSampleSchema(SchemaBase):
    """
    Schema representation for a model result sample.
    """
    starttime = fields.DateTime(format='iso')
    endtime = fields.DateTime(format='iso')
    erate = fields.Nested(QuakeMLRealQuantitySchema())
    b = fields.Nested(QuakeMLRealQuantitySchema())


class ReservoirSchema(SchemaBase):
    """
    Schema representation for a reservoir.
    """
    # XXX(damb): WKT/WKB
    geom = fields.String()
    samples = fields.Nested(ModelResultSampleSchema, many=True)
    sub_geometries = fields.Nested('self', many=True)

    @post_dump(pass_original=True)
    def geom_as_wkt(self, data, orig):
        """
        Use the :code:`WKT` representation of the reservoir geometry instead of
        :code:`WKB`.
        """
        try:
            data['geom'] = orig.wkt()
        except AttributeError:
            pass

        return data


class SFMWorkerOMessageSchema(SchemaBase):
    """
    Schema implementation for de-/serializing
    :py:class:`ramsis.sfm.worker.model.ModelResult`.
    """
    status = fields.Str()
    status_code = fields.Int()
    data = fields.Dict(keys=fields.UUID(),
                       values=fields.Nested(ReservoirSchema))
    length = fields.Int()
    warning = fields.Str()
