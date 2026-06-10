from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserInDBBase(UserBase):
    id: UUID
    total_credits: int
    is_admin: bool

    class Config:
        from_attributes = True

class User(UserInDBBase):
    pass
