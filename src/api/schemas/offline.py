from typing import List

from pydantic import BaseModel

class DiscreteMove(BaseModel):
    steps: int
    steering: float
    acceleration: float

class OfflineScenarioPreview(BaseModel):
    scenario_id: int
    moves: List[DiscreteMove]