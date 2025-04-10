from typing import List

from models.offline_scenario import OfflineScenarioMoveSequence, OfflineScenarioMove
from db.scenario_repository import ScenarioRepository
from database import async_session
from schemas.offline import OfflineScenarioPreview, DiscreteMove
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from db.scenario_repository import ScenarioRepository

class OfflineScheduler:


    @classmethod
    async def get_global_move(cls, scenario_id: int, vehicle_id: int) -> OfflineScenarioMoveSequence:
        async with async_session() as session:
            self_move = await cls.get_active_move(session, scenario_id, vehicle_id)
            global_move = await cls.collect_move(session, self_move)

            if global_move:
                for seq in global_move:
                    seq.is_executed = True

                await session.commit()
                sequence_lengths = [moveseq.total_steps() for moveseq in global_move]
                sequence_jsons = [moveseq.model_dump() for moveseq in global_move]

                min_length = min(sequence_lengths)

                print(sequence_lengths)
                multiplayer_sequence = {
                    'steps': min_length,
                    'moves': sequence_jsons,
                }
                return multiplayer_sequence
            return None

    @classmethod
    async def collect_move(cls, session, self_move: OfflineScenarioMoveSequence):
        scenario_db = await ScenarioRepository.get_scenario(session, self_move.scenario_id)
        vehicles_ids = [vehicle.id for vehicle in scenario_db.vehicles]
        vehicles_ids.remove(self_move.vehicle_id)
        move_seqs = [self_move]
        for vehicle_id in vehicles_ids:
            move_seq = await cls.get_active_move(session, scenario_db.id, vehicle_id)
            if not move_seq:
                return None

            move_seqs.append(move_seq)

        return move_seqs



    @classmethod
    async def get_active_move(cls, session, scenario_id: int, vehicle_id: int):
        query = select(OfflineScenarioMoveSequence).options(joinedload(OfflineScenarioMoveSequence.moves)).where(
            OfflineScenarioMoveSequence.scenario_id == scenario_id,
            OfflineScenarioMoveSequence.vehicle_id == vehicle_id,
            OfflineScenarioMoveSequence.is_executed == False
        )

        res = await session.execute(query)
        move_seq = res.unique().scalar_one_or_none()

        return move_seq


    @classmethod
    async def save_move(cls, move):
        async with async_session() as session:
            if await cls.get_active_move(session, move.scenario_id, move.vehicle_id):
                return
            scenario_db = OfflineScenarioMoveSequence(
                scenario_id=move.scenario_id,
                vehicle_id=move.vehicle_id,
            )
            session.add(scenario_db)
            await session.commit()
            await session.refresh(scenario_db)
            await cls.assign_moves(session, scenario_db.id, move.moves)

    @classmethod
    async def assign_moves(cls, session, sequence_id:int, moves: List[DiscreteMove]):
        moves_db = [OfflineScenarioMove(
            steps=move.steps,
            acceleration=move.acceleration,
            steering=move.steering,
            sequence_id=sequence_id,
        ) for move in moves]

        session.add_all(moves_db)
        await session.commit()


