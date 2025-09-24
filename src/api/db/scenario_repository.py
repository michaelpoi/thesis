from typing import List

from database import async_session
from fastapi import HTTPException
from sqlalchemy import select, or_
from models.scenario import Scenario, Map, Vehicle
from sqlalchemy.orm import joinedload


class ScenarioRepository:

    @classmethod
    async def get_users_scenario(cls, user_id):
            async with async_session() as session:
                stmt = (
                    select(Scenario)
                    .options(
                        joinedload(Scenario.vehicles),
                        joinedload(Scenario.map),
                    )
                    .join(Vehicle, Vehicle.scenario_id == Scenario.id)
                    .where(
                        Vehicle.assigned_user_id == user_id                       
                    )
                )
                result = await session.execute(stmt)
                return result.unique().scalars().all()

    @classmethod
    async def get_all(cls):
        async with async_session() as session:
            queryset = await session.execute(
                select(Scenario).options(joinedload(Scenario.vehicles), joinedload(Scenario.map))
            )

        return queryset.unique().scalars().all()

    @classmethod
    async def create_scenario(cls, scenario: Scenario, vehicles):
        async with async_session() as session:
            result = await session.execute(select(Map).where(Map.id == scenario.map_id))
            map_obj = result.scalar_one_or_none()
            if not map_obj:
                raise HTTPException(status_code=404, detail="Map not found")
            # Add the scenario first
            session.add(scenario)
            await session.commit()  # Commit to generate the scenario.id
            await session.refresh(scenario)  # Refresh the scenario to get the id back


            await cls.assign_vehicles(session, vehicles, scenario.id)

            scenario = await cls.get_scenario(session, scenario.id)

        return scenario




    @classmethod
    async def assign_vehicles(cls, session, vehicles: List[Vehicle], scenario_id: int):
        for vehicle in vehicles:
            # Ensure that vehicles have the correct foreign key (scenario_id)
            vehicle.scenario_id = scenario_id  # Set foreign key before adding to session
            vehicle.id = None

        # Add vehicles to the session
        try:
            session.add_all(vehicles)
            await session.commit()  # Commit vehicles
        except:
            await session.rollback()
            raise HTTPException(status_code=400, detail="Assigned User not found")



    @classmethod
    async def get_scenario(cls, session, scenario_id: int):
        result = await session.execute(
            select(Scenario).options(joinedload(Scenario.vehicles), joinedload(Scenario.map)).filter(
                Scenario.id == scenario_id)
        )
        scenario_db = result.unique().scalar_one()

        return scenario_db