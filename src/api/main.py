import asyncio
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from uvicorn import Config, Server
from settings import settings
from database import init_db, deinit_db
from routers.scenarios import router as tasks_router
from routers.auth import router as auth_router
from routers.maps import router as maps_router
from routers.offline_scenarios import router as offline_router
from utils import create_admin, create_map
from db.offline_response import blob_adapter

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await create_admin()
    await create_map()
    yield
    await deinit_db()
    blob_adapter.clear_all()

app = FastAPI(
    title="My API",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

origins = [
    "http://localhost:3000",  # React app on localhost
    "http://127.0.0.1:3000",  # React app alternative
    "http://0.0.0.0:3000",  # Deployed frontend app
    "http://127.0.0.1",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allowed origins
    allow_credentials=True,  # Allow cookies/auth credentials
    allow_methods=["*"],  # Allowed HTTP methods
    allow_headers=["*"],  # Allowed HTTP headers
)

app.include_router(tasks_router, prefix='/api')
app.include_router(auth_router, prefix='/api')
app.include_router(maps_router, prefix='/api')
app.include_router(offline_router, prefix='/api')

async def main():
    config = Config(app=app,host=settings.host, port=settings.port, reload=settings.debug)
    server = Server(config=config)
    await server.serve()



if __name__ == '__main__':
    asyncio.run(main())
