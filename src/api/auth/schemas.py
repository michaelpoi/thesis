from pydantic import BaseModel

class User(BaseModel):
    id: int
    username: str

class UserInDB(User):
    hashed_password: str

class AddUser(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

