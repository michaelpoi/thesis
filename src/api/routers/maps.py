import os

from fastapi.exceptions import HTTPException

from fastapi import APIRouter, UploadFile, File
from schemas.maps import BaseMap as SAddMap, Map as SMap, NamedMap as SNamedMap
from schemas.results import Scenario as SScenario

from models.scenario import Map
from db.map_repository import MapRepository

from models.scenario import ScenarioStatus
from sim.manager import map_preview
from cache.maps import map_cache

router = APIRouter(
    prefix='/maps',
    tags=['maps']
)

@router.get('/')
async def list_maps():
    return await MapRepository.get_all_maps()

@router.delete('/{map_id}')
async def delete_map(map_id: int):
    await MapRepository.delete_map(map_id)

    return {'message': 'Map deleted'}


@router.post("/")
async def create_map(smap: SNamedMap):
    map_db = await MapRepository.create_map(smap.label, smap.layout)

    return get_full_map(map_db)


def get_full_map(map_db: Map):

    map_db = Map(id = map_db.id, layout= map_db.layout)

    # We need to put a scenario to the queue to get a simulation result
    # => create random scenario that is never stored in db

    sample_scenario = SScenario(id=1231,
                                vehicles=[],
                                owner_id=1232,
                                steps=1000,
                                map=map_db,
                                status=ScenarioStatus.FINISHED
                                )
    
    blob = map_preview(sample_scenario)

    map_schema = SMap(id=map_db.id, layout=map_db.layout, blob=blob)

    return map_schema



@router.put("/{map_id}")
async def update_map(map_id: int, smap: SAddMap):
    map_obj = await MapRepository.update_map(map_id, smap.layout)

    map_cache.invalidate(map_id)

    return get_full_map(map_obj)

@router.get('/{map_id}')
async def preview_map(map_id: int):
    map_db = await MapRepository.get_map_by_id(map_id)
    if not map_db:
        raise HTTPException(status_code=404, detail="Map not found")

    return get_full_map(map_db)
