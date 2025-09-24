from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from auth.schemas import Token, User as SUser
from auth.auth import authenticate_user, create_access_token
from fastapi.security import OAuth2PasswordRequestForm

from auth.auth import get_current_user, get_current_admin

from settings import settings

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@router.post("/login", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data = {"sub": user.username},
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")



@router.get("/me", response_model=SUser)
async def me(user=Depends(get_current_admin)):
    return user

@router.get("/user", response_model=SUser)
async def me(user=Depends(get_current_user)):
    return user
