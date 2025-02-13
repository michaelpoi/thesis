from typing import List

from fastapi.exceptions import HTTPException
from fastapi.websockets import WebSocket, WebSocketDisconnect
from fastapi import APIRouter, Depends

from models import scenario
from models.scenario import Scenario, Vehicle
from database import async_session
from schemas.results import Scenario as SScenario, Vehicle as SVehicle
from sqlalchemy.future import select
from queues.tasks import queue
from sqlalchemy.orm import joinedload
from schemas.results import Move

router = APIRouter(
    prefix='/tasks',
    tags=['tasks']
)


@router.post('/')
async def create_scenario(scenario: SScenario) -> SScenario:
    # Convert Pydantic model to dict, remove the 'id' field and 'vehicles' list
    scenario_json = scenario.model_dump()
    scenario_json.pop('id')  # Remove 'id' from the input as it is auto-generated
    vehicles_json = scenario_json.pop('vehicles')  # Extract the 'vehicles' list

    # Create Scenario instance (without vehicles)
    scenario_db = Scenario(**scenario_json)

    # Create a list of Vehicle instances
    vehicles = [
        Vehicle(scenario_id=scenario_db.id, **vehicle)
        for vehicle in vehicles_json
    ]

    # Using async session to commit the transaction
    async with async_session() as session:
        # Add the scenario first
        session.add(scenario_db)
        await session.commit()  # Commit to generate the scenario.id
        await session.refresh(scenario_db)  # Refresh the scenario to get the id back

        # After the scenario is created, link the vehicles to the scenario
        for vehicle in vehicles:
            # Ensure that vehicles have the correct foreign key (scenario_id)
            vehicle.scenario_id = scenario_db.id  # Set foreign key before adding to session
            vehicle.id = None

        # Add vehicles to the session
        session.add_all(vehicles)
        await session.commit()  # Commit vehicles

        # Re-fetch the scenario with vehicles loaded using joinedload
        result = await session.execute(
            select(Scenario).options(joinedload(Scenario.vehicles)).filter(Scenario.id == scenario_db.id)
        )
        scenario_db = result.unique().scalar_one()

    scenario_schema = SScenario.model_validate(scenario_db)
    await queue.send_task(scenario_schema, "CREATE ENV")
    # Now the scenario has the vehicles linked, and we return the scenario
    return scenario_db


@router.get('/')
async def list_all_tasks() -> List[SScenario]:
    async with async_session() as session:
        queryset = await session.execute(
            select(Scenario).options(joinedload(Scenario.vehicles))
        )

    return queryset.unique().scalars().all()

clients = {}
@router.websocket('/ws/{task_id}/{vehicle_id}/')
async def connect_task(websocket: WebSocket, task_id: int, vehicle_id: int):
    async with async_session() as session:
        queryset = await session.execute(select(Scenario).where(Scenario.id == task_id))
        task = queryset.scalars().one_or_none()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        vehicle = await session.execute(select(Vehicle).where(Vehicle.id == vehicle_id))

        vehicle = vehicle.scalars().one_or_none()

        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")

        if vehicle.scenario_id != task.id:
            raise HTTPException(status_code=404, detail="Vehicle incorrect")

        await websocket.accept()

        if not task_id in clients:
            clients[task_id] = []

        clients[task_id].append(websocket)

        while True:
            try:
                data = await websocket.receive_text()
                move = Move(scenario_id=task_id, vehicle_id=vehicle_id, direction=data)
                await queue.send_task(move, "MOVE")
            except WebSocketDisconnect:
                # await websocket.close()
                break





