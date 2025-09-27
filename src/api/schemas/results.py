from typing import List, Optional

from pydantic import BaseModel, Field
from schemas.maps import Map
from constants import Constants

class Vehicle(BaseModel):
    id: int = Field(None)
    init_x: int
    init_y: int
    init_speed: float
    assigned_user_id: Optional[int]
    is_terminated: Optional[bool] = False

    class Config:
        from_attributes = True

class ScenarioBase(BaseModel):
    steps: int
    vehicles: List[Vehicle]
    map: int
    is_offline: bool = False


class Scenario(ScenarioBase):
    id: Optional[int] = 5
    owner_id: Optional[int] = None
    status: Optional[str]
    map: Map

    class Config:
        from_attributes = True

class Move(BaseModel):
    scenario_id: int
    vehicle_id: int
    direction: str
    timestamp: Optional[int]
    sens_acceleration: Optional[float] = Constants.RealTime.MOVE_ACCELERATION_SENSITIVITY
    sens_steering: Optional[float] = Constants.RealTime.MOVE_STEERING_SENSITIVITY

class SimulationTask(BaseModel):
    id: int
    scenario: Scenario
