from typing import List, Optional

from pydantic import BaseModel, Field

class Vehicle(BaseModel):
    id: int = Field(None)
    init_x: int
    init_y: int
    init_speed: float

    class Config:
        from_attributes = True

class Scenario(BaseModel):
    id: Optional[int] = 5
    steps: int
    vehicles: List[Vehicle]

    class Config:
        from_attributes = True

class Move(BaseModel):
    scenario_id: int
    vehicle_id: int
    direction: str

class SimulationTask(BaseModel):
    id: int
    scenario: Scenario
