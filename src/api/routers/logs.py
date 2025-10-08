from fastapi import APIRouter, Depends
from fastapi.responses import Response, FileResponse
from db.scenario_repository import ScenarioRepository
from models.scenario import ScenarioStatus
from utils import get_log_filename
from auth.auth import get_current_admin

from database import async_session

router = APIRouter(
    prefix="/logs",
    tags=["logs"],
)

@router.get('/{scenario_id}')
async def get_log(scenario_id: int, user=Depends(get_current_admin)):
    async with async_session() as session:
        scenario_db = await ScenarioRepository.get_scenario(session, scenario_id)
    
    if scenario_db.status != ScenarioStatus.FINISHED:
        return Response(status=404)
    
    prefix = None
    if scenario_db.is_offline:
        prefix = "offline"

    abs, filename = get_log_filename(scenario_db.id, prefix)

    return FileResponse(abs, media_type='application/json', filename=filename)

    