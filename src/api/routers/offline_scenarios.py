from typing import List

from fastapi import APIRouter
from fastapi.responses import Response

from schemas.offline import OfflineScenarioPreview, DiscreteMove
from schemas.results import Scenario as SScenario, Vehicle as SVehicle

from database import async_session
from db.scenario_repository import ScenarioRepository
from queues.queue import queue

router = APIRouter(
    prefix="/offline",
    tags=["offline"]
)

@router.post('/init/{scenario_id}')
async def init_scenario(scenario_id: int):
    async with async_session() as session:
        scenario_db = await ScenarioRepository.get_scenario(session, scenario_id)

        scenario = SScenario.model_validate(scenario_db)
        await queue.send_init(scenario, mtype='offline')
        return scenario


@router.post('/preview')
async def get_preview(move: OfflineScenarioPreview):
    await queue.send_offline_move(move, is_preview=True)
    image_bytes = await queue.wait_for_image()

    return Response(content=image_bytes, media_type="image/png")



@router.post('/submit')
async def post_preview(preview: OfflineScenarioPreview):
    await queue.send_offline_move(preview)
    image_bytes = await queue.wait_for_image()
    if not image_bytes:
        return {'ok': False}
    print(image_bytes)

    return Response(content=image_bytes, media_type="image/png")

