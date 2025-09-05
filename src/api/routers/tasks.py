
from typing import List
import asyncio
from fastapi.websockets import WebSocket, WebSocketDisconnect
from fastapi import APIRouter, Depends

from db.scenario_repository import ScenarioRepository
from datetime import datetime

from models.scenario import Scenario, Vehicle
from database import async_session
from schemas.results import Scenario as SScenario, Vehicle as SVehicle, ScenarioBase as SScenarioAdd
from sqlalchemy.future import select
from queues.queue import queue
from queues.images import queue as img_queue
from schemas.results import Move
from auth.auth import get_current_user
from routers.utils.connection import ConnectionManager
from sim.worker import Worker

from models.scenario import ScenarioStatus
from plot.renderer import Renderer

router = APIRouter(
    prefix='/tasks',
    tags=['tasks']
)


@router.post('/')
async def create_scenario(scenario: SScenarioAdd, user=Depends(get_current_user)) -> SScenario:
    # Convert Pydantic model to dict, remove the 'id' field and 'vehicles' list
    scenario_json = scenario.model_dump()
    vehicles_json = scenario_json.pop('vehicles')  # Extract the 'vehicles' list
    map_id = scenario_json.pop('map')

    # Create Scenario instance (without vehicles)
    scenario = Scenario(**scenario_json, owner_id=user.id, map_id=map_id)

    # Create a list of Vehicle instances
    vehicles = [
        Vehicle(scenario_id=scenario.id, **vehicle)
        for vehicle in vehicles_json
    ]
    # Using async session to commit the transaction
    scenario_db = await ScenarioRepository.create_scenario(scenario, vehicles)
    # scenario_schema = SScenario.model_validate(scenario_db)
    # Now the scenario has the vehicles linked, and we return the scenario
    return scenario_db


@router.get('/')
async def list_all_tasks() -> List[SScenario]:
    return await ScenarioRepository.get_all()

manager = ConnectionManager()


@router.websocket('/ws/{task_id}/{vehicle_id}/')
async def connect_task(websocket: WebSocket, task_id: int, vehicle_id: int):
    token = websocket.headers.get('sec-websocket-protocol')

    try:
        user = await get_current_user(token)


    except Exception:
        await websocket.close(code=4001)
        return

    async with async_session() as session:
        scenario_db = await ScenarioRepository.get_scenario(session, task_id)

        if scenario_db.status == ScenarioStatus.FINISHED:
            await websocket.close(code=1008)
            return

        scenario_db.status = ScenarioStatus.STARTED

        await session.commit()

        scenario_schema = SScenario.model_validate(scenario_db)

        vehicle = await session.execute(select(Vehicle)
                                        .where(Vehicle.id == vehicle_id))

        vehicle = vehicle.scalars().one_or_none()

        if not vehicle:
            return await websocket.close()

        if vehicle.scenario_id != scenario_db.id:
            return await websocket.close()
        

        await manager.connect(task_id, token, websocket)


        # await queue.send_init(scenario_schema)

        worker = Worker(scenario_schema)
        worker.setup_env()
        worker.setup_vehicle()

        rendered = Renderer()

        while True:
            try:
                start = datetime.now()
                try:
                    data = await asyncio.wait_for(websocket.receive_json(), 0.5) # TODO: 
                    dir = data.get('direction')
                    time = data.get('timestamp')
                except asyncio.TimeoutError:
                    time = None
                    dir = "KEEP_ALIVE"

                # await session.refresh(scenario_db) could slow things down

                move = Move(scenario_id=task_id, vehicle_id=vehicle_id, direction=dir, timestamp=time)
                state = worker.process_move(move)

            
                if state:
                    start = datetime.now()
                    plt_json= rendered.get_dict(state['state'])
                    data = {
                        'plt': plt_json,
                        'time': move.timestamp
                    }
                    await manager.broadcast_json(task_id, data)
                    print(f"Broadcast time: {datetime.now() - start}")
                else:
                    print('Scenario Finished')
                    await websocket.close(code=1008)
                    return
                
            except WebSocketDisconnect:
                manager.disconnect(task_id, websocket)
                await websocket.close()
                return


from fastapi.responses import FileResponse
@router.get('/image/')
def get_image():
    return FileResponse('/app/output.png', media_type='image/png')




