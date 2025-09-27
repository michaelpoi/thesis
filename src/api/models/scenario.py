from models.base import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Float, Enum, Boolean
from sqlalchemy.orm import relationship
import enum

# class SampleTask(Base):
#     __tablename__ = 'sample_task'
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     name = Column(String)

class ScenarioStatus(enum.Enum):
    CREATED = "CREATED"
    STARTED = "STARTED"
    FINISHED = "FINISHED"

class Scenario(Base):
    __tablename__ = 'scenario'
    id = Column(Integer, primary_key=True, autoincrement=True)
    steps = Column(Integer)
    vehicles = relationship('Vehicle', back_populates='scenario')
    owner_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    owner = relationship('User')
    map_id = Column(Integer, ForeignKey('map.id'), nullable=False)
    map = relationship('Map')
    status = Column(Enum(ScenarioStatus), nullable=False, default=ScenarioStatus.CREATED)
    is_offline = Column(Boolean)
    # map = Column(String, nullable=False)

class Map(Base):
    __tablename__ = 'map'
    id = Column(Integer, primary_key=True, autoincrement=True)
    layout = Column(String, nullable=False)
    label = Column(String, nullable=True)

class Vehicle(Base):
    __tablename__ = 'vehicle'
    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario_id = Column(Integer, ForeignKey('scenario.id'))
    init_x = Column(Integer)
    init_y = Column(Integer)
    init_speed = Column(Float)
    scenario = relationship('Scenario', back_populates='vehicles')
    assigned_user_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    is_terminated = Column(Boolean, default=False)
