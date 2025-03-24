from typing import List, Optional

from pydantic import BaseModel, Field
from schemas.maps import Map

class Vehicle(BaseModel):
    id: int = Field(None)
    init_x: int
    init_y: int
    init_speed: float
    assigned_user_id: Optional[int]

    class Config:
        from_attributes = True

class ScenarioBase(BaseModel):
    steps: int
    vehicles: List[Vehicle]
    map: int


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

class SimulationTask(BaseModel):
    id: int
    scenario: Scenario
