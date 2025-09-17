from typing import List
import json
from fastapi import APIRouter
from fastapi.responses import Response

from schemas.offline import OfflineScenarioPreview, DiscreteMove
from schemas.results import Scenario as SScenario, Vehicle as SVehicle

from database import async_session
from db.scenario_repository import ScenarioRepository
from queues.queue import queue
from db.offline_repository import OfflineScheduler
from sim.manager import offline_manager
from plot.renderer import Renderer

router = APIRouter(
    prefix="/offline",
    tags=["offline"]
)

@router.post('/init/{scenario_id}')
async def init_scenario(scenario_id: int):
    async with async_session() as session:
        scenario_db = await ScenarioRepository.get_scenario(session, scenario_id)

        scenario = SScenario.model_validate(scenario_db)
        offline_manager.register_worker(scenario)
        # await queue.send_init(scenario, mtype='offline')
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

    await OfflineScheduler.save_move(preview)
    # collected_move =  await OfflineScheduler.get_global_move(preview.scenario_id, preview.vehicle_id)
    total_steps = sum([prv.steps for prv in preview.moves])
    collected_move = {
        "steps": total_steps,
        "moves":[
            preview.model_dump()
        ],
        "is_preview": False
    }
    
    if collected_move:
        state = offline_manager.process_move(collected_move, scenario_id=preview.scenario_id)

        renderer = Renderer()

        response = renderer.get_rendering_data(state)
   

        return response
    return {}

