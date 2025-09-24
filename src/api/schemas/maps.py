from typing import Optional

from pydantic import BaseModel

class BaseMap(BaseModel):
    layout: str

class Map(BaseMap):
    id: int
    blob: Optional[dict] = None

    class Config:
        from_attributes = True

class NamedMap(BaseMap):
    label: Optional[str] = None

    class Config:
        from_attributes = True
