from db.user_repository import UserRepository

async def create_admin():
    try:
        await UserRepository.create_user("admin", "admin")
    except ValueError:
        pass
