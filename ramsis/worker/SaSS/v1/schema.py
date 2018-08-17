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

from ramsis.utils.protocol import WorkerInputMessageSchema as \
    _WorkerInputMessageSchema


class ShapiroModelParameterSchema(Schema):
    x = fields.Float(required=True)

    class Meta:
        ordered = True

# class ShapiroModelParameterSchema


class WorkerInputMessageSchema(_WorkerInputMessageSchema):
    model_parameters = fields.Nested(ShapiroModelParameterSchema,
                                     required=True)


# ---- END OF <schema.py> ----
