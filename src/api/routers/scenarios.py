
from typing import List
import asyncio
from fastapi.websockets import WebSocket, WebSocketDisconnect
from fastapi import APIRouter, Depends
import logging

from db.scenario_repository import ScenarioRepository
from datetime import datetime

from models.scenario import Scenario, Vehicle
from database import async_session
from schemas.results import Scenario as SScenario, Vehicle as SVehicle, ScenarioBase as SScenarioAdd
from sqlalchemy.future import select
from schemas.results import Move
from auth.auth import get_current_user, get_current_admin
from routers.utils.connection import ConnectionManager
from sim.workers.worker import Worker
from sim.manager import manager as sim_manager

from models.scenario import ScenarioStatus
from plot.renderer import Renderer
from constants import Constants

router = APIRouter(
    prefix='/tasks',
    tags=['tasks']
)


@router.post('/')
async def create_scenario(scenario: SScenarioAdd, user=Depends(get_current_admin)) -> SScenario:
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
async def list_all_tasks(admin=Depends(get_current_admin)) -> List[SScenario]:
    return await ScenarioRepository.get_all()

manager = ConnectionManager()

@router.get('/mine')
async def users_tasks(user=Depends(get_current_user)):
    return await ScenarioRepository.get_users_scenario(user.id)


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



        sim_manager.register_worker(scenario_schema)

        rendered = Renderer()

        # Lobby check
        required = len([v for v in scenario_schema.vehicles if v.assigned_user_id])
        
        while (curr := manager.count_connections(task_id)) < required:
            await manager.broadcast_json(task_id, {
                "status": "WAITING",
                "connected": curr,
                "required": required
            })

            await asyncio.sleep(1)

        while True:
            try:
                try:
                    data = await asyncio.wait_for(websocket.receive_json(), Constants.RealTime.WS_MOVE_TIMEOUT) 
                    dir = data.get('direction')
                    a, s = data.get('sens_acceleration', None), data.get('sens_steering', None)
                    time = data.get('timestamp')
                except asyncio.TimeoutError:
                    time = None
                    dir = "KEEP_ALIVE"
                    a, s = None, None


                move = Move(scenario_id=task_id,
                             vehicle_id=vehicle_id, 
                             direction=dir, 
                             timestamp=time, 
                             sens_acceleration=a,
                             sens_steering=s
                            )
                state = sim_manager.process_move(move)

            
               
                data = rendered.get_rendering_data(state, move.timestamp)

                if state['status'] == "ACTIVE":
                    await manager.broadcast_json(task_id, data)

                if state['status'] == "FINISHED":
                    scenario_db.status = ScenarioStatus.FINISHED
                    await session.commit()
                    await manager.broadcast_json(task_id, data)
                    await manager.close_all(task_id)
                    return

                if state['status'] == "TERMINATED":
                    logging.info(f"Vehicle {vehicle_id} terminated in scenario {task_id}")
                    await manager.send_personal_message(data, websocket)
                    await manager.disconnect(task_id, websocket)
                    return
                
            except WebSocketDisconnect:
                await manager.disconnect(task_id, websocket)
                return






