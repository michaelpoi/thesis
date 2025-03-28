from db.user_repository import UserRepository
from db.map_repository import MapRepository

async def create_admin():
    try:
        await UserRepository.create_user("admin", "admin")
    except ValueError:
        pass

async def create_map():
    await MapRepository.create_map(label="line", layout="SSS")
