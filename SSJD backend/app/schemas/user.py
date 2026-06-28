from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    society_id: int
    name: str
    email: EmailStr
    password: str
    role: Optional[str] = "admin"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    society_id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool

    class Config:
        from_attributes = True
