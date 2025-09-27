from db.user_repository import UserRepository
from fastapi import APIRouter, Depends, HTTPException
from auth.auth import get_current_admin
from auth.schemas import AddUser, User as SUser


router = APIRouter(
    prefix='/users',
    tags=['users']
)

@router.get('/')
async def list_all_users(user=Depends(get_current_admin)):
    return await UserRepository.get_all()

@router.post("/", response_model=SUser)
async def register(user: AddUser, creator=Depends(get_current_admin)):
    try:
        user =  await UserRepository.create_user(user.username, user.password, user.is_admin)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return user


@router.delete('/{user_id}')
async def remove_user(user_id: int, remover=Depends(get_current_admin)):
    await UserRepository.remove_user(user_id)
    return {}


