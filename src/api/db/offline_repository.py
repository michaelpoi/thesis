from typing import List


from models.offline_scenario import OfflineScenarioMoveSequence, OfflineScenarioMove
from db.scenario_repository import ScenarioRepository
from database import async_session
from schemas.offline import OfflineScenarioPreview, DiscreteMove
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from db.scenario_repository import ScenarioRepository
from sqlalchemy.orm import attributes
import logging

class OfflineScheduler:

    @classmethod
    async def total_steps_db(cls, session, seq_id: int) -> int:
        return await session.scalar(
            select(func.coalesce(func.sum(OfflineScenarioMove.steps), 0))
            .where(OfflineScenarioMove.sequence_id == seq_id)
        ) or 0
    
    @classmethod
    def seq_to_dict(cls, moveseq):
        if not moveseq:
            return None
        return OfflineScenarioPreview.from_orm(moveseq).model_dump()


    @classmethod
    async def get_global_move(cls, scenario_id: int, vehicle_id: int) -> OfflineScenarioMoveSequence:
        async with async_session() as session:
            self_move = await cls.get_active_move(session, scenario_id, vehicle_id)
            global_move = await cls.collect_move(session, self_move)

            if global_move:
                sequence_lengths = [await cls.total_steps_db(session, moveseq.id) for moveseq in global_move]
                logging.warning(sequence_lengths)
                min_length = min(sequence_lengths)
                sequences_to_exec = []
                next_move = None

                for seq in global_move:
                    seq.is_executed = True
                    if seq.total_steps() > min_length:
                        first, second = await cls.split_move_sequence(session, seq, min_length)
                        first.is_executed = True
                        sequences_to_exec.append(first)

                        if seq.vehicle_id == vehicle_id:
                            next_move = cls.seq_to_dict(second)
                        

                    else:
                        sequences_to_exec.append(seq)

                    

                await session.commit()
                
                sequence_jsons = [cls.seq_to_dict(moveseq) for moveseq in sequences_to_exec]

                print(sequence_lengths)
                multiplayer_sequence = {
                    'steps': min_length,
                    'moves': sequence_jsons,
                    'next': next_move
                }

                return multiplayer_sequence
            return None

    @classmethod
    async def collect_move(cls, session, self_move: OfflineScenarioMoveSequence):
        scenario_db = await ScenarioRepository.get_scenario(session, self_move.scenario_id)
        vehicles_ids = [vehicle.id for vehicle in scenario_db.vehicles if vehicle.assigned_user_id and not vehicle.is_terminated]
        vehicles_ids.remove(self_move.vehicle_id)
        move_seqs = [self_move]
        for vehicle_id in vehicles_ids:
            move_seq = await cls.get_active_move(session, scenario_db.id, vehicle_id)
            if not move_seq:
                logging.warning(f"No move from {vehicle_id}")
                return None

            move_seqs.append(move_seq)

        return move_seqs



    @classmethod
    async def get_active_move(cls, session, scenario_id: int, vehicle_id: int, editable=False):
        '''
        Returns user`s move that is not executed yet
        '''
        q = (
            select(OfflineScenarioMoveSequence)
            .options(joinedload(OfflineScenarioMoveSequence.moves))
            .where(
                OfflineScenarioMoveSequence.scenario_id == scenario_id,
                OfflineScenarioMoveSequence.vehicle_id == vehicle_id,
                OfflineScenarioMoveSequence.is_executed.is_(False),
                OfflineScenarioMoveSequence.is_editable.is_(editable),
            )
            .order_by(OfflineScenarioMoveSequence.id.desc())
            .limit(1)
        )
        res = await session.execute(q)
        latest = res.scalars().first()

        # res = await session.execute(query)
        # move_seq = res.unique().scalar_one_or_none()

        if latest and editable:
            latest.is_editable = False
            await session.commit()

        return latest


    @classmethod
    async def save_move(cls, move):
        '''
        Save single user move in database
        '''
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
        '''
        Helper function to append moves to existing sequence
        '''
        moves_db = [OfflineScenarioMove(
            steps=move.steps,
            acceleration=move.acceleration,
            steering=move.steering,
            sequence_id=sequence_id,
        ) for move in moves]

        session.add_all(moves_db)
        await session.commit()


    @classmethod
    async def split_move_sequence(cls, session, move_sequence:OfflineScenarioMoveSequence, k: int):
        '''
            Function splits move sequence into 2 move sequences and stores to db
        '''

        def clone_move(move, steps):
            return OfflineScenarioMove(
                steps=steps,
                steering=move.steering,
                acceleration = move.acceleration,
                sequence_id = None
            )
        

        curr_steps = 0
        first_moves = []
        second_moves = []

        for ind, move in enumerate(move_sequence.moves):
            if curr_steps + move.steps < k:
                first_moves.append(clone_move(move, move.steps))
                curr_steps += move.steps

            else:
                steps_first = k - curr_steps

                if steps_first > 0:
                    move_first = clone_move(move, steps_first)

                    first_moves.append(move_first)
                
                steps_second = move.steps - steps_first

                if steps_second > 0:
                    move_second = clone_move(move, steps_second)

                    second_moves.append(move_second)

                for m in move_sequence.moves[ind+1:]:
                    second_moves.append(m)

                break


        first_seq = OfflineScenarioMoveSequence(
            scenario_id = move_sequence.scenario_id,
            vehicle_id = move_sequence.vehicle_id,
            is_editable = False
        )

        second_seq = OfflineScenarioMoveSequence(
            scenario_id = move_sequence.scenario_id,
            vehicle_id = move_sequence.vehicle_id,
            is_editable = True
        )

        session.add_all([first_seq, second_seq])
        await session.flush()  # assign PKs without expiring

        # Set foreign keys directly; do NOT access first_seq.moves / second_seq.moves
        for m in first_moves:
            m.sequence_id = first_seq.id
        for m in second_moves:
            m.sequence_id = second_seq.id

        session.add_all(first_moves + second_moves)
        await session.flush()  # persist children

        # Mark collections as loaded in-memory to avoid any lazy IO later
        attributes.set_committed_value(first_seq, "moves", first_moves)
        attributes.set_committed_value(second_seq, "moves", second_moves)

        await session.delete(move_sequence)
        await session.flush()

        return first_seq, second_seq
    











