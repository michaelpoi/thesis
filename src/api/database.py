from contextlib import asynccontextmanager

from settings import settings
from models import Base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

engine = create_async_engine(settings.db_url)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_session():
    async with async_session() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def deinit_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)




