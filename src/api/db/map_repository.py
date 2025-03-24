from database import async_session
from schemas.maps import Map as SMap, NamedMap
from models.scenario import Map
from sqlalchemy import Select, Delete


class MapRepository:
    @classmethod
    async def get_all_maps(cls):
        async with async_session() as session:
            queryset = await session.execute(Select(Map))
            maps = queryset.unique().scalars().all()
        return maps

    @classmethod
    async def delete_map(cls, map_id: int):
        async with async_session() as session:
            await session.execute(Delete(Map).where(Map.id == map_id))
            await session.commit()

    @classmethod
    async def create_map(cls, label: str, layout: str):
        async with async_session() as session:
            map_db = Map(label=label, layout=layout)
            session.add(map_db)
            await session.commit()
            await session.refresh(map_db)

        return map_db

    @classmethod
    async def update_map(cls, map_id: int, layout: str):
        async with async_session() as session:
            map_obj = await session.get(Map, map_id)
            if not map_obj:
                raise ValueError("Map not found")

            map_obj.layout = layout

            await session.commit()

        return map_obj

    @classmethod
    async def get_map_by_id(cls, map_id: int):
        async with async_session() as session:
            queryset = await session.execute(Select(Map).where(Map.id == map_id))
            map_db = queryset.scalar_one_or_none()

        return map_db

    @classmethod
    async def set_map_image(cls, map_id:int, filename:str):
        async with async_session() as session:
            result = await session.execute(Select(Map).where(Map.id == map_id))
            map_obj = result.scalar()
            map_obj.image = filename
            await session.commit()

