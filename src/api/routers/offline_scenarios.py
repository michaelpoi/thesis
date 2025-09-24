from typing import List
import logging
from fastapi import APIRouter
from fastapi.responses import Response

from schemas.offline import OfflineScenarioPreview, DiscreteMove
from schemas.results import Scenario as SScenario, Vehicle as SVehicle

from database import async_session
from db.scenario_repository import ScenarioRepository
from db.offline_repository import OfflineScheduler
from sim.manager import offline_manager
from plot.renderer import Renderer
from cache.offline import blob_adapter
from models.scenario import ScenarioStatus

router = APIRouter(
    prefix="/offline",
    tags=["offline"]
)

# TODO: remove it later
@router.post('/init/{scenario_id}')
async def init_scenario(scenario_id: int):
    async with async_session() as session:
        scenario_db = await ScenarioRepository.get_scenario(session, scenario_id)

        scenario = SScenario.model_validate(scenario_db)
        offline_manager.register_worker(scenario)
        return scenario


@router.post('/preview')
async def get_preview(move: OfflineScenarioPreview):
    move_json = move.model_dump()
    move_json['is_preview'] = True

    state = offline_manager.process_move(move_json, scenario_id=move.scenario_id)

    renderer = Renderer()

    response = renderer.get_rendering_data(state)

    return response


@router.post('/submit')
async def post_preview(preview: OfflineScenarioPreview):
    logging.warning(preview)
    await OfflineScheduler.save_move(preview)
    collected_move =  await OfflineScheduler.get_global_move(preview.scenario_id, preview.vehicle_id)
    # total_steps = sum([prv.steps for prv in preview.moves])
    # collected_move = {
    #     "steps": total_steps,
    #     "moves":[
    #         preview.model_dump()
    #     ],
    #     "is_preview": False
    # }
    
    if collected_move:
        collected_move['is_preview'] = False
        next = collected_move.pop('next', None)
        state = offline_manager.process_move(collected_move, scenario_id=preview.scenario_id)
        
        if state['status'] == 'FINISHED':
            async with async_session() as session:
                scenario_db = await ScenarioRepository.get_scenario(session, preview.scenario_id)
                scenario_db.status = ScenarioStatus.FINISHED
                await session.commit()

        renderer = Renderer()

        response = renderer.get_rendering_data(state)

        blob_adapter.save_blob(preview.scenario_id, response)

        turn = blob_adapter.latest_turn(preview.scenario_id)
   

        return {"turn": turn, "data": response, "next": next}
    return {}


@router.get('/ping/{scenario_id}/{vehicle_id}/{turn}')
async def ping(scenario_id: int, vehicle_id: int, turn: int):
    latest = blob_adapter.latest_turn(scenario_id)
    if latest is None or latest < turn:
        return Response(status_code=304)  # nothing new
    blob = blob_adapter.get_by_turn(scenario_id, latest)
    async with async_session() as session:
        next_move = await OfflineScheduler.get_active_move(session, scenario_id, vehicle_id, editable=True)
                                                    

    # include the latest turn so the client can update its cursor
    return {"turn": latest, 
            "data": blob, 
            "next": OfflineScheduler.seq_to_dict(next_move)}


