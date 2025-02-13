from typing import List

from pydantic import BaseModel

class VehiclePosition(BaseModel):
    vehicle_id: int
    x: int
    y: int
    speed: int

class ScenarioStep(BaseModel):
    scenario_id: int
    step: int
    vehicles: List[VehiclePosition]

class Move(BaseModel):
    scenario_id: int
    vehicle_id: int
    direction: str

class Vehicle(BaseModel):
    id: int
    init_x: int
    init_y: int
    init_speed: float

class InitEnv(BaseModel):
    id: int
    steps: int
    vehicles: List[Vehicle]
