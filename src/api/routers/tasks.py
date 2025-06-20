import base64
from typing import List
import asyncio
import io
from fastapi.exceptions import HTTPException
from fastapi.websockets import WebSocket, WebSocketDisconnect
from fastapi import APIRouter, Depends

from db.scenario_repository import ScenarioRepository

from models import scenario
from models.scenario import Scenario, Vehicle, Map
from database import async_session
from schemas.results import Scenario as SScenario, Vehicle as SVehicle, ScenarioBase as SScenarioAdd
from sqlalchemy.future import select
from queues.queue import queue
from queues.images import queue as img_queue
from sqlalchemy.orm import joinedload
from schemas.results import Move
from auth.auth import get_current_user
from PIL import Image

from models.scenario import ScenarioStatus

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

clients = {}
@router.websocket('/ws/{task_id}/{vehicle_id}/')
async def connect_task(websocket: WebSocket, task_id: int, vehicle_id: int):
    token = websocket.headers.get('sec-websocket-protocol')

    try:
        user = await get_current_user(token)
        print(f"Websocket user {user}")

    except Exception:
        await websocket.close(code=4001)
    print(token)

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

        await websocket.accept(subprotocol=token)

        if not task_id in clients:
            clients[task_id] = []

        clients[task_id].append(websocket)

        await queue.send_init(scenario_schema)

        while True:
            try:
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), 0.1)
                except asyncio.TimeoutError:
                    data = "KEEP_ALIVE"

                await session.refresh(scenario_db)
                # if scenario_db.status == ScenarioStatus.FINISHED:
                #     print("Scenario finished")
                #     await websocket.close(code=1008)

                move = Move(scenario_id=task_id, vehicle_id=vehicle_id, direction=data)
                print(move)
                await queue.send_move(move)
                try:
                    current_frame = await asyncio.wait_for(img_queue.consume_results(task_id), 0.5)
                except:
                    print("Timed out")
                    continue

                if not current_frame:
                    continue

                if current_frame['alive']:
                    await websocket.send_bytes(current_frame['image'])
                else:
                    print('Scenario Finished')
                    await websocket.close(code=1008)
                # try:
                #     image = Image.open(f"/app/{scenario_db.id}.png")
                #     img_bytes = io.BytesIO()
                #     image.save(img_bytes, format="PNG")  # Convert to PNG format
                #     img_bytes.seek(0)  # Reset cursor to start of the file
                #
                #     # Send the image as bytes
                #
                #     # Send the JSON message
                #     await websocket.send_bytes(img_bytes)
                # except:
                #     pass
            except WebSocketDisconnect:
                clients[task_id].remove(websocket)
                #await websocket.close()
                break


from fastapi.responses import FileResponse
@router.get('/image/')
def get_image():
    return FileResponse('/app/output.png', media_type='image/png')




