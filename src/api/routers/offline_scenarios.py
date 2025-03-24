from fastapi import APIRouter

from schemas.offline import OfflineScenarioPreview

router = APIRouter(
    prefix="/offline",
    tags=["offline"]
)

@router.post('/<scenario_id>')
async def init_scenario(scenario_id: int):
    # TODO: this endpoint should send message to the simulation to initialize main worker
    # Returns: initial scenario setup
    pass

@router.get('/preview/<scenario_id>')
async def get_preview(scenario_id: int, preview: OfflineScenarioPreview):
    # TODO: this endpoint should send signal to simulation to run preview worker
    # Returns: preview GIF or just final state
    pass

@router.post('/preview/<scenario_id>')
async def post_preview(scenario_id: int, preview: OfflineScenarioPreview):
    # TODO: Submit suitable sequence of moves to be processes by main worker
    # Returns: GIF or final state
    pass

