from models.base import Base
from sqlalchemy import Column, Integer, ForeignKey, Boolean, String, Float
from sqlalchemy.orm import relationship


class OfflineScenarioMoveSequence(Base):
    __tablename__ = 'offline_scenario_sequence'

    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario_id = Column(Integer, ForeignKey('scenario.id', ondelete='CASCADE'))
    scenario = relationship('Scenario')
    vehicle_id = Column(Integer, ForeignKey('vehicle.id', ondelete='CASCADE'))
    vehicle = relationship('Vehicle')

    moves = relationship('OfflineScenarioMove', back_populates='sequence', cascade='all, delete-orphan', passive_deletes=True)
    is_executed = Column(Boolean, default=False)
    is_editable = Column(Boolean, default=False)

    def total_steps(self):
        return sum([move.steps for move in self.moves])


class OfflineScenarioMove(Base):
    __tablename__ = "offline_scenario_move"

    id = Column(Integer, primary_key=True, autoincrement=True)
    acceleration = Column(Float)
    steering = Column(Float)
    steps = Column(Integer)

    sequence_id = Column(Integer, ForeignKey('offline_scenario_sequence.id', ondelete='CASCADE'))
    sequence = relationship('OfflineScenarioMoveSequence', back_populates='moves')


class ExecutedStep(Base):
    __tablename__ = 'executed_step'
    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario_id = Column(Integer, ForeignKey('scenario.id'))
    scenario = relationship('Scenario')
    step_num = Column(Integer)
    image_url = Column(String, nullable=True)


