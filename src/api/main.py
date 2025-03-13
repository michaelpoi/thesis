import asyncio
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from uvicorn import Config, Server
from settings import settings
from database import init_db, deinit_db
from routers.tasks import router as tasks_router
from routers.auth import router as auth_router
from routers.maps import router as maps_router
from queues.images import queue
from utils import create_admin

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await create_admin()
    yield
    await deinit_db()

os.makedirs(settings.static_dir, exist_ok=True)
app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=settings.static_folder), name="static")

origins = [
    "http://localhost:3000",  # React app on localhost
    "http://127.0.0.1:3000",  # React app alternative
    "http://0.0.0.0:3000",  # Deployed frontend app
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allowed origins
    allow_credentials=True,  # Allow cookies/auth credentials
    allow_methods=["*"],  # Allowed HTTP methods
    allow_headers=["*"],  # Allowed HTTP headers
)

app.include_router(tasks_router)
app.include_router(auth_router)
app.include_router(maps_router)

async def main():
    config = Config(app=app,host=settings.host, port=settings.port, reload=settings.debug)
    server = Server(config=config)
    await asyncio.gather(
        server.serve(),
        queue.consume_results()
    )



if __name__ == '__main__':
    asyncio.run(main())
