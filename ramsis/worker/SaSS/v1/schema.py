# This is <schema.py>
# -----------------------------------------------------------------------------
#
# Purpose: SaSS schema facilities.
#
# Copyright (c) Daniel Armbruster (SED, ETH), Lukas Heiniger (SED, ETH)
#
# REVISION AND CHANGES
# 2018/04/16        V0.1    Daniel Armbruster
# =============================================================================

from marshmallow import fields, Schema

from ramsis.worker.SaSS import core
from ramsis.utils.protocol import WorkerInputMessageSchema as \
    _WorkerInputMessageSchema


class TupleField(fields.Field):

    def __init__(self, entries, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._entries = entries

    def _deserialize(self, value, attr=None, data=None):
        return tuple(
            field._deserialize(val, attr, data) for field, val in
            zip(self._entries, value))

# class TupleField


# FIXME(damb): Set default parameters.

# NOTE(damb): Since we (Philipp Kästli, Lukas Heiniger and me (damb)) decided
# keeping both model_parameters and the reservoir geometry under the model's
# responsability model_defaults configurerd at the worker's CLI are handled
# with higher preceedence than parameters configured from webserver clients.
# That is why parameters are not configured with required=True. (Parameters
# intentionally required are commented, bellow.)
#
# However, since the interface already existed, we still provide this
# interface.
#
class ShapiroModelParameterSchema(Schema):
    const_magnitude_binning = fields.Float(
        default=core.DEFAULT_MAG_BINNING)

    # dim-x, dim-y, dim-z in meters
    const_dim_voxel = TupleField(
        [fields.Float(required=True), fields.Float(required=True),
         fields.Float(required=True)], default=core.DEFAULT_DIM_VOXEL)

    # ----
    #XXX(damb): Forecast specific parameters
    # Optional threshold for magnitudes to be taken into consideration;
    # default: the catalog's magnitude of completeness
    fc_threshold_magnitude = fields.Float()
    # Threshold in m^3/min below it is assumend that the pumps have shut-in; to
    # account for sampling errors
    fc_threshold_simulation = fields.Float(
        default=core.DEFAULT_THRESHOLD_STIMULATION)
    # Hysteresis: Total number of earthquakes from previous forcast periods
    fc_hysteresis_total_num_forcast_earthquakes = fields.Int(
        default=core.DEFAULT_HYSTERESIS_TOTAL_NUM_EQ)
    # Cumulative injected volume Q_c(t)
    #fc_cumulative_injected_volume = fields.Int(required=True)
    fc_cumulative_injected_volume = fields.Int()
    # Default datetime the forecast is started
    # TODO(damb): Check if the parameter is already passed to the worker within
    # the Forecast(Input)Schema
    fc_datetime_start = fields.DateTime(default=core.DEFAULT_FORECAST_START)
    # ----
    #XXX(damb): Training specific parameters
    # duration of the training period (in days)
    training_duration = fields.Float()
    #training_duration = fields.Float(required=True)
    # number of kernels to perform the learning with
    training_num_kernels = fields.Int(
        default=core.DEFAULT_NUM_KERNELS)

    class Meta:
        ordered = True

# class ShapiroModelParameterSchema


class WorkerInputMessageSchema(_WorkerInputMessageSchema):
    #model_parameters = fields.Nested(ShapiroModelParameterSchema,
    #                                 required=True)
    model_parameters = fields.Nested(ShapiroModelParameterSchema)


# ---- END OF <schema.py> ----
