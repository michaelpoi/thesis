
from typing import List, Optional

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
    assigned_user_id: Optional[int]

class Map(BaseModel):
    id: int
    layout: str
    image: Optional[str]

class InitEnv(BaseModel):
    id: int
    steps: int
    vehicles: List[Vehicle]
    map: Map

class DiscreteMove(BaseModel):
    steps: int
    steering: float
    acceleration: float

class OfflineScenarioPreview(BaseModel):
    scenario_id: int
    vehicle_id: int
    moves: List[DiscreteMove]


