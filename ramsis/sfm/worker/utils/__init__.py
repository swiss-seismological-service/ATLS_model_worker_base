# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
General purpose ramsis.sfm.workers utilities
"""
import argparse
import collections
import enum
import functools
import logging
import pkg_resources

from marshmallow import Schema, fields, post_dump, validate, pre_load


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
    CONTEXT_DELIMITER = '::'

    def process(self, msg, kwargs):
        if isinstance(self.extra['ctx'], collections.Sequence):
            prefix = self.CONTEXT_DELIMITER.join(
                f"{c}" for c in self.extra['ctx'])
        else:
            prefix = '%s' % self.extra['ctx']
        return '[%s] %s' % (prefix, msg), kwargs


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

    class Meta:
        strict = True
        ordered = True

    @classmethod
    def remove_empty(self, data):
        """
        Filter out fields with empty (e.g. :code:`None`, :code:`[], etc.)
        values.
        """
        return {k: v for k, v in data.items() if v or
                isinstance(v, (int, float))}

    @classmethod
    def _flatten_dict(cls, data, sep='_'):
        """
        Flatten a a nested dict :code:`dict` using :code:`sep` as key
        separator.
        """
        retval = {}
        for k, v in data.items():

            if isinstance(v, dict):
                sub_k = list(v.keys())[0]
                if sub_k in ['value', 'uncertainty', 'upperuncertainty',
                             'loweruncertainty', 'confidencelevel']:
                    for sub_k, sub_v in cls._flatten_dict(v, sep).items():
                        retval[k + sep + sub_k] = sub_v
                else:
                    retval[k] = v
            else:
                retval[k] = v

        return retval

    @classmethod
    def _nest_dict(cls, data, sep='_'):
        """
        Nest a dictionary by splitting the key on a delimiter.
        """
        retval = {}
        for k, v in data.items():
            t = retval
            prev = None
            if k in ['status_code']:
                t.setdefault(k, v)
                continue
            for part in k.split(sep):
                if prev is not None:
                    t = t.setdefault(prev, {})
                prev = part
            else:
                t.setdefault(prev, v)

        return retval

    @post_dump
    def postdump(self, data, **kwargs):
        filtered_data = self.remove_empty(data)
        nested_data = self._nest_dict(filtered_data, sep='_')
        return nested_data

    @pre_load
    def preload(self, data, **kwargs):
        flattened_data = self._flatten_dict(data, sep='_')
        return flattened_data


class ModelResultSampleSchema(SchemaBase):
    """
    Schema representation for a model result sample.
    """
    starttime = fields.DateTime(format='iso')
    endtime = fields.DateTime(format='iso')
    numberevents_value = fields.Float(required=True)
    numberevents_uncertainty = Positive()
    numberevents_loweruncertainty = Positive()
    numberevents_upperuncertainty = Positive()
    numberevents_confidencelevel = Percentage()

    hydraulicvol_value = fields.Float(required=True)
    hydraulicvol_uncertainty = Positive()
    hydraulicvol_loweruncertainty = Positive()
    hydraulicvol_upperuncertainty = Positive()
    hydraulicvol_confidencelevel = Percentage()

    b_value = fields.Float(required=True)
    b_uncertainty = Positive()
    b_loweruncertainty = Positive()
    b_upperuncertainty = Positive()
    b_confidencelevel = Percentage()

    a_value = fields.Float(required=True)
    a_uncertainty = Positive()
    a_loweruncertainty = Positive()
    a_upperuncertainty = Positive()
    a_confidencelevel = Percentage()

    mc_value = fields.Float(required=True)
    mc_uncertainty = Positive()
    mc_loweruncertainty = Positive()
    mc_upperuncertainty = Positive()
    mc_confidencelevel = Percentage()


class ReservoirSchema(SchemaBase):
    """
    Schema representation for a reservoir.
    """
    # XXX(damb): WKT/WKB
    geom = fields.String()
    samples = fields.Nested(ModelResultSampleSchema, many=True)
    sub_geometries = fields.Nested('self', many=True)

    @post_dump(pass_original=True)
    def geom_as_wkt(self, data, orig, **kwargs):
        """
        Use the :code:`WKT` representation of the reservoir geometry instead of
        :code:`WKB`.
        """
        try:
            data['geom'] = orig.wkt()
        except AttributeError:
            pass

        return data


class SFMWorkerResponseDataAttributesSchema(SchemaBase):
    """
    Schema representation of the SFM worker response data attributes.
    """
    status = fields.Str()
    status_code = fields.Int()
    forecast = fields.Nested(ReservoirSchema)
    warning = fields.Str()


class SFMWorkerResponseDataSchema(SchemaBase):
    """
    Schema representation fo the SFM worker response data.
    """
    id = fields.UUID()
    attributes = fields.Nested(SFMWorkerResponseDataAttributesSchema)


class SFMWorkerOMessageSchema(SchemaBase):
    """
    Schema implementation for de-/serializing
    :py:class:`ramsis.sfm.worker.model.ModelResult`.
    """
    data = fields.Method("_serialize_data")
    errors = fields.Dict()
    meta = fields.Dict()

    def _serialize_data(self, obj):
        if 'data' in obj:
            if isinstance(obj['data'], list):
                return SFMWorkerResponseDataSchema(
                    context=self.context, many=True).dump(obj['data'])

            return SFMWorkerResponseDataSchema(
                context=self.context).dump(obj['data'])


class ResponseData(collections.namedtuple(
        'ResponseData', ['id', 'attributes'])):

    @classmethod
    def no_content(cls):
        return cls(id=None, attributes=None)

    @classmethod
    def accepted(cls, task_id):
        attributes = {
            'status_code': StatusCode.TaskAccepted.value,
            'status': StatusCode.TaskAccepted.name}

        return cls(id=task_id, attributes=attributes)

    @classmethod
    def from_task(cls, task):
        attributes = {
            'status_code': task.status_code,
            'status': task.status,
            'forecast': task.result,
            'warning': task.warning}

        return cls(id=task.id, attributes=attributes)
