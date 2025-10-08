from typing import List
import logging
from fastapi import APIRouter, Depends
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
from auth.auth import get_current_user

router = APIRouter(
    prefix="/offline",
    tags=["offline"]
)

# TODO: remove it later
@router.post('/init/{scenario_id}')
async def init_scenario(scenario_id: int, user=Depends(get_current_user)):
    async with async_session() as session:
        scenario_db = await ScenarioRepository.get_scenario(session, scenario_id)

        scenario = SScenario.model_validate(scenario_db)
        offline_manager.register_worker(scenario)
        return scenario


@router.post('/preview')
async def get_preview(move: OfflineScenarioPreview, user=Depends(get_current_user)):
    move_json = move.model_dump()
    move_json['is_preview'] = True

    state = offline_manager.process_move(move_json, scenario_id=move.scenario_id)

    renderer = Renderer()

    response = renderer.get_rendering_data(state)

    return response


async def get_tm_status(session, state, scenario_id, vehicle_id):
    if tm_info := state.get('tm_info', None):
        logging.warning(f"TM info: {tm_info}")
        reason = tm_info.get(vehicle_id, None)
        if reason:
            await ScenarioRepository.set_vehicle_as_terminated(session, scenario_id, int(vehicle_id))
            return reason
    return None


@router.post('/submit')
async def post_preview(preview: OfflineScenarioPreview, user=Depends(get_current_user)):
    logging.warning(preview)
    async with async_session() as session:
        tm = await ScenarioRepository.is_vehicle_terminated(session, preview.scenario_id, preview.vehicle_id)
        if tm:
            return Response(status=405)
        await OfflineScheduler.save_move(preview)
        collected_move =  await OfflineScheduler.get_global_move(preview.scenario_id, preview.vehicle_id)
        
        if collected_move:
            tm = None
            collected_move['is_preview'] = False
            next = collected_move.pop('next', None)
            state = offline_manager.process_move(collected_move, scenario_id=preview.scenario_id)
            
            if state['status'] == 'FINISHED':
                scenario_db = await ScenarioRepository.get_scenario(session, preview.scenario_id)
                scenario_db.status = ScenarioStatus.FINISHED
                await session.commit()

            tm = await get_tm_status(session, state, preview.scenario_id, preview.vehicle_id)
            logging.warning(f"Tm: {tm} for {preview.vehicle_id}")

            renderer = Renderer()

            response = renderer.get_rendering_data(state)

            blob_adapter.save_blob(preview.scenario_id, response)

            turn = blob_adapter.latest_turn(preview.scenario_id)
    

            return {"turn": turn, "data": response, "next": next, "tm": tm}
        return {}


@router.get('/ping/{scenario_id}/{vehicle_id}/{turn}')
async def ping(scenario_id: int, vehicle_id: int, turn: int, user=Depends(get_current_user)):
    latest = blob_adapter.latest_turn(scenario_id)
    if latest is None or latest < turn:
        return Response(status_code=304)  # nothing new
    blob = blob_adapter.get_by_turn(scenario_id, latest)
    async with async_session() as session:
        tm = await get_tm_status(session, blob, scenario_id, str(vehicle_id))
        logging.warning(f"Tm: {tm} for {vehicle_id}")
        next_move = await OfflineScheduler.get_active_move(session, scenario_id, vehicle_id, editable=True)
                                                    

    # include the latest turn so the client can update its cursor
    return {"turn": latest, 
            "data": blob, 
            "next": OfflineScheduler.seq_to_dict(next_move),
            "tm": tm}


