from typing import List

from pydantic import BaseModel

class DiscreteMove(BaseModel):
    steps: int
    steering: float
    acceleration: float

    class Config:
        from_attributes = True

class OfflineScenarioPreview(BaseModel):
    scenario_id: int
    vehicle_id: int
    moves: List[DiscreteMove]

    class Config:
        from_attributes = True
