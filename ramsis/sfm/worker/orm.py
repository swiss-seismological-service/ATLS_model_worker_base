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
from sqlalchemy.orm import relationship
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
                          order_by='Reservoir.parent_ref')

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
    starttime = Column(DateTime)
    endtime = Column(DateTime)
    numberevents_value = Column(Float, nullable=False)
    numberevents_uncertainty = Column(Float)
    numberevents_loweruncertainty = Column(Float)
    numberevents_upperuncertainty = Column(Float)
    numberevents_confidencelevel = Column(Float)

    hydraulicvol_value = Column(Float, nullable=False)
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
    parent_ref = Column(Integer, ForeignKey('reservoir.oid'))
    geom = Column(Geometry(geometry_type='GEOMETRYZ', dimension=3,
                  management=True), nullable=False)

    samples = relationship('ramsis.sfm.worker.orm.ModelResultSample',
                           back_populates='reservoir',
                           order_by='ModelResultSample.starttime')

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
