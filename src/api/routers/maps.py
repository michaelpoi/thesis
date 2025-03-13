import os

from fastapi.exceptions import HTTPException

from anyio.streams import file
from fastapi import APIRouter, UploadFile, File
from schemas.maps import BaseMap as SAddMap, Map as SMap, NamedMap as SNamedMap
from database import async_session
from sqlalchemy import Select, Delete
import asyncio
from schemas.results import Scenario as SScenario
from queues.queue import queue

from models.scenario import Map
from settings import settings

router = APIRouter(
    prefix='/maps',
    tags=['maps']
)

@router.get('/')
async def list_maps():
    async with async_session() as session:
        queryset = await session.execute(Select(Map))
        maps = queryset.unique().scalars().all()
    return maps

@router.delete('/{map_id}')
async def delete_map(map_id: int):
    async with async_session() as session:
        await session.execute(Delete(Map).where(Map.id == map_id))
        await session.commit()

    return {'message': 'Map deleted'}


@router.post("/")
async def create_map(map: SNamedMap):
    map_db = Map(**map.model_dump())

    async with async_session() as session:
        session.add(map_db)
        await session.commit()
        await session.refresh(map_db)


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
                                )

    await queue.send_init(sample_scenario)



@router.put("/{map_id}")
async def update_map(map_id: int, smap: SAddMap):
    async with async_session() as session:
        map_obj = await session.get(Map, map_id)
        if not map_obj:
            raise HTTPException(status_code=404, detail="Map not found")

        map_obj.layout = smap.layout

        await session.commit()

    await queue_map_preview(map_obj)

    return map_obj

@router.get('/{map_id}')
async def preview_map(map_id: int):
    async with async_session() as session:
        queryset = await session.execute(Select(Map).where(Map.id == map_id))
        map_db = queryset.scalar_one_or_none()
        if not map_db:
            raise HTTPException(status_code=404, detail="Map not found")

    sample_scenario = SScenario(id=1231,
                                vehicles=[],
                                owner_id=1232,
                                steps=1000,
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

    async with async_session() as session:
        result = await session.execute(Select(Map).where(Map.id == map_id))
        map_obj = result.scalar()
        map_obj.image = filename
        await session.commit()

    return {"filename": filename}