from models.base import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship

class SampleTask(Base):
    __tablename__ = 'sample_task'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

class Scenario(Base):
    __tablename__ = 'scenario'
    id = Column(Integer, primary_key=True, autoincrement=True)
    steps = Column(Integer)
    vehicles = relationship('Vehicle', back_populates='scenario')
    owner_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    owner = relationship('User')

class Vehicle(Base):
    __tablename__ = 'vehicle'
    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario_id = Column(Integer, ForeignKey('scenario.id'))
    init_x = Column(Integer)
    init_y = Column(Integer)
    init_speed = Column(Float)
    scenario = relationship('Scenario', back_populates='vehicles')
    assigned_user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
