from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    society_id: int
    name: str
    email: EmailStr
    password: str
    role: Optional[str] = "admin"


class UserResponse(BaseModel):
    id: int
    society_id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool

    class Config:
        from_attributes = True
