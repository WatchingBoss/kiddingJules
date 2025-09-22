from pydantic import BaseModel

class UserCreate(BaseModel):
    login: str
    password: str
