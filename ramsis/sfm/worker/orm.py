# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
ORM facilities.
"""

import datetime
import uuid

from geoalchemy2 import Geometry
from osgeo import ogr
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
                          single_parent=True)

    model = relationship("ramsis.sfm.worker.orm.Model",
                         back_populates="tasks")

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


class RealQuantity(ORMBase):
    """
    ORM mapping representing a :py:code:`QuakeMLRealQuantity`.
    """
    value = Column(Float, nullable=False)
    uncertainty = Column(Float)
    loweruncertainty = Column(Float)
    upperuncertainty = Column(Float)
    confidencelevel = Column(Float)


class ModelResultSample(ORMBase):
    """
    ORM mapping representing a single sample of a model result.
    """
    starttime = Column(DateTime)
    endtime = Column(DateTime)
    rate_id = Column(Integer, ForeignKey('realquantity.oid'))
    rate = relationship('ramsis.sfm.worker.orm.RealQuantity',
                        backref=backref('_modelresultsample_rate',
                                        uselist=False),
                        foreign_keys=[rate_id])

    b_id = Column(Integer, ForeignKey('realquantity.oid'))
    b = relationship('ramsis.sfm.worker.orm.RealQuantity',
                     backref=backref('_modelresultsample_b',
                                     uselist=False),
                     foreign_keys=[b_id])

    reservoir_id = Column(Integer, ForeignKey('reservoir.oid'))
    reservoir = relationship('ramsis.sfm.worker.orm.Reservoir',
                             back_populates='samples')


class Reservoir(LastSeenMixin, ORMBase):
    """
    RAMSIS worker reservoir geometry ORM mapping.
    """
    parent_ref = Column(Integer, ForeignKey('reservoir.oid'))
    geom = Column(Geometry(geometry_type='GEOMETRYZ', dimension=3),
                  nullable=False)

    samples = relationship('ramsis.sfm.worker.orm.ModelResultSample',
                           back_populates='reservoir')

    sub_geometries = relationship('ramsis.sfm.worker.orm.Reservoir')

    def wkt(self):
        try:
            return ogr.CreateGeometryFromWkb(
                self.geom._data_from_desc(self.geom.desc)).ExportToWkt()
        except AttributeError:
            return self.geom

    def __repr__(self):
        return "<{}(geom={}, sub_geoms={})>".format(type(self).__name__,
                                                    self.wkt(),
                                                    self.sub_geometries)
