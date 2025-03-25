import os

from fastapi.exceptions import HTTPException

from fastapi import APIRouter, UploadFile, File
from schemas.maps import BaseMap as SAddMap, Map as SMap, NamedMap as SNamedMap
from database import async_session
from schemas.results import Scenario as SScenario
from queues.queue import queue

from models.scenario import Map
from settings import settings
from db.map_repository import MapRepository

from models.scenario import ScenarioStatus

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


    # Send preview map image signal
    await queue_map_preview(map_db)

    return map_db


async def queue_map_preview(map_db: Map):

    map_schema = Map(id = map_db.id, image=None, layout= map_db.layout)

    # We need to put a scenario to the queue to get a simulation result
    # => create random scenario that is never stored in db

    sample_scenario = SScenario(id=1231,
                                vehicles=[],
                                owner_id=1232,
                                steps=1000,
                                map=map_schema,
                                status=ScenarioStatus.FINISHED
                                )

    await queue.send_init(sample_scenario)



@router.put("/{map_id}")
async def update_map(map_id: int, smap: SAddMap):
    map_obj = await MapRepository.update_map(map_id, smap.layout)

    await queue_map_preview(map_obj)

    return map_obj

@router.get('/{map_id}')
async def preview_map(map_id: int):
    map_db = await MapRepository.get_map_by_id(map_id)
    if not map_db:
        raise HTTPException(status_code=404, detail="Map not found")

    sample_scenario = SScenario(id=1231,
                                vehicles=[],
                                owner_id=1232,
                                steps=1000,
                                status=ScenarioStatus.FINISHED,
                                map=Map(id=map_db.id, layout=map_db.layout, image=None),
                                )
    await queue.send_init(scenario=sample_scenario)

    return

@router.post("/{map_id}")
async def upload_map_image(map_id: int, image: UploadFile = File(...)):
    filename = f"{map_id}.png"
    filepath = settings.static_dir / filename

    if os.path.exists(filepath):
        os.remove(filepath)

    with open(filepath, "wb+") as f:
        f.write(image.file.read())

    await MapRepository.set_map_image(map_id, filename)

    return {"filename": filename}