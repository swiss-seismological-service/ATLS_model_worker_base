# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
ORM facilities.
"""

import datetime
import uuid

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr, declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.types import TypeDecorator, CHAR

from ramsis.sfm.worker.utils import StatusCode


class GUID(TypeDecorator):
    """
    Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.
    """
    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value


# -----------------------------------------------------------------------------
class Base(object):

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    oid = Column(Integer, primary_key=True)


class LastSeenMixin(object):

    @declared_attr
    def lastseen(cls):
        return Column(DateTime, default=datetime.datetime.utcnow,
                      onupdate=datetime.datetime.utcnow)


ORMBase = declarative_base(cls=Base)


# -----------------------------------------------------------------------------
class Task(LastSeenMixin, ORMBase):
    """
    RAMSIS worker task ORM mapping.
    """
    id = Column(GUID, unique=True, index=True)
    status = Column(String, nullable=False)
    status_code = Column(Integer, nullable=False)
    warning = Column(String)
    model_ref = Column(Integer, ForeignKey('model.oid'))
    result_ref = Column(Integer, ForeignKey('reservoir.oid'))

    result = relationship("ramsis.sfm.worker.orm.Reservoir", uselist=False,
                          cascade="all, delete, delete-orphan",
                          single_parent=True,
                          order_by='Reservoir.parentref')

    model = relationship("ramsis.sfm.worker.orm.Model",
                         back_populates="tasks",
                         order_by='Model.name')

    @classmethod
    def new(cls, id, model):
        return cls(id=id, status=StatusCode.TaskAccepted.name,
                   status_code=StatusCode.TaskAccepted.value,
                   model=model)

    @classmethod
    def pending(cls, id, model):
        return cls(id=id, status=StatusCode.TaskProcessing.name,
                   status_code=StatusCode.TaskProcessing.value,
                   model=model)

    def __repr__(self):
        return "<{}(id={})>".format(type(self).__name__, self.id)


class Model(ORMBase):
    """
    RAMSIS worker model ORM mapping.
    """
    name = Column(String, unique=True)
    description = Column(String)

    tasks = relationship("ramsis.sfm.worker.orm.Task",
                         back_populates="model")

    def __repr__(self):
        return "<{}(name={})>".format(type(self).__name__, self.name)


class ModelResultSample(ORMBase):
    """
    ORM mapping representing a single sample of a model result.
    """
    starttime = Column(DateTime, nullable=False)
    endtime = Column(DateTime, nullable=False)
    numberevents_value = Column(Float)
    numberevents_uncertainty = Column(Float)
    numberevents_loweruncertainty = Column(Float)
    numberevents_upperuncertainty = Column(Float)
    numberevents_confidencelevel = Column(Float)

    hydraulicvol_value = Column(Float)
    hydraulicvol_uncertainty = Column(Float)
    hydraulicvol_loweruncertainty = Column(Float)
    hydraulicvol_upperuncertainty = Column(Float)
    hydraulicvol_confidencelevel = Column(Float)

    b_value = Column(Float, nullable=False)
    b_uncertainty = Column(Float)
    b_loweruncertainty = Column(Float)
    b_upperuncertainty = Column(Float)
    b_confidencelevel = Column(Float)

    a_value = Column(Float, nullable=False)
    a_uncertainty = Column(Float)
    a_loweruncertainty = Column(Float)
    a_upperuncertainty = Column(Float)
    a_confidencelevel = Column(Float)

    mc_value = Column(Float, nullable=False)
    mc_uncertainty = Column(Float)
    mc_loweruncertainty = Column(Float)
    mc_upperuncertainty = Column(Float)
    mc_confidencelevel = Column(Float)

    reservoir_id = Column(Integer, ForeignKey('reservoir.oid'))
    reservoir = relationship('ramsis.sfm.worker.orm.Reservoir',
                             back_populates='samples')


class Reservoir(LastSeenMixin, ORMBase):
    """
    RAMSIS worker reservoir geometry ORM mapping.
    """
    oid = Column(Integer, primary_key=True)
    parentref = Column(Integer, ForeignKey('reservoir.oid'))

    x_min = Column(Float)
    x_max = Column(Float)
    y_min = Column(Float)
    y_max = Column(Float)
    z_min = Column(Float)
    z_max = Column(Float)

    samples = relationship('ramsis.sfm.worker.orm.ModelResultSample',
                           back_populates='reservoir',
                           order_by='ModelResultSample.starttime')

    subgeometries = relationship('ramsis.sfm.worker.orm.Reservoir',
                                 backref=backref('parent', remote_side=[oid]))

    def __repr__(self):
        return ("<{}(x_min={}, x_max={}, y_min={}, y_max={}, z_min={}, "
                "z_max={}, sub_geoms={})>".format(
                    type(self).__name__,
                    self.x_min,
                    self.x_max,
                    self.y_min,
                    self.y_max,
                    self.z_min,
                    self.z_max,
                    self.subgeometries))
