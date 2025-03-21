from typing import Optional

from passlib.context import CryptContext
from sqlalchemy.future import select

from models.user import User
from database import async_session
from auth.schemas import User as SUser, UserInDB


class UserRepository:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @classmethod
    async def get_user_by_id(cls, user_id:int) -> Optional[SUser]:
        async with async_session() as session:
            query = select(User).where(User.id == user_id)
            result = await session.execute(query)
            user = result.scalars().one_or_none()

        if not user:
            return None

        return SUser(id=user.id, username=user.username)

    @classmethod
    async def get_user_by_username(cls, username:str) -> Optional[SUser]:
        async with async_session() as session:
            query = select(User).where(User.username == username)
            result = await session.execute(query)
            user = result.scalars().one_or_none()

        if not user:
            return None

        return SUser(id=user.id, username=user.username)

    @classmethod
    async def get_db_user(cls, username:str) -> UserInDB | None:
        async with async_session() as session:
            query = select(User).where(User.username == username)
            result = await session.execute(query)
            user = result.scalars().one_or_none()
            if not user:
                return None
        return UserInDB(id=user.id, username=user.username, hashed_password=user.hashed_password)

    @classmethod
    def hash_password(cls,password: str) -> str:
        return cls.pwd_context.hash(password)

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        return cls.pwd_context.verify(plain_password, hashed_password)


    @classmethod
    async def create_user(cls, username:str, password:str) -> SUser:
        if await cls.get_user_by_username(username):
            raise ValueError("User already exists")

        await cls.password_validator(password)
        hashed_password = cls.hash_password(password)

        async with async_session() as session:
            db_user = User(username=username, hashed_password=hashed_password)
            session.add(db_user)
            await session.commit()
            await session.refresh(db_user)

        return SUser(id=db_user.id, username=db_user.username)


    @classmethod
    async def password_validator(cls, password:str) -> None:
        # TODO: add real validation here
        if len(password) < 5:
            raise ValueError("Password must be at least 5 characters")




