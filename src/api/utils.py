from db.user_repository import UserRepository
from db.map_repository import MapRepository
from db.scenario_repository import ScenarioRepository
from settings import settings
from models.scenario import Scenario, Vehicle
import logging

async def create_admin():
    logging.info("Creating default users...")
    try:
        await UserRepository.create_user(settings.default_user_name, settings.default_user_password, True)
        await UserRepository.create_user("user1", "user1")
    except ValueError:
        pass

async def create_map():
    logging.info("Creating default maps...")
    await MapRepository.create_map(label="line", layout="SSS")
    await MapRepository.create_map(label="round", layout="SOS")


async def create_default_scenarios():
    logging.info("Creating default scenarios...")
    scenario = Scenario(steps=1000, 
                        owner_id=1, 
                        map_id=1, 
                        is_offline=False)
    
    vehicles = [
        Vehicle(init_x=25, init_y=0, init_speed=0, assigned_user_id=1),
        Vehicle(init_x=50, init_y=0, init_speed=0, assigned_user_id=2)
    ]

    await ScenarioRepository.create_scenario(scenario, vehicles)

    off_scenario = Scenario(steps=1000, 
                        owner_id=1, 
                        map_id=1, 
                        is_offline=True)
    
    off_vehicles = [
        Vehicle(init_x=25, init_y=0, init_speed=0, assigned_user_id=1),
        Vehicle(init_x=50, init_y=0, init_speed=0, assigned_user_id=2)
    ]

    await ScenarioRepository.create_scenario(off_scenario, off_vehicles)
    


def get_log_filename(scenario_id, prefix=None):
    filename = f"scenario_{scenario_id}.json"
    filename = prefix + filename if prefix else filename
    log_path = settings.logs_dir / filename

    return log_path, filename