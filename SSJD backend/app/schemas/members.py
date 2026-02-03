from pydantic import BaseModel
from typing import Optional


class MemberCreate(BaseModel):
    name: str
    phone: str
    address: Optional[str] = None


class MemberUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class MemberResponse(BaseModel):
    id: int
    name: str
    phone: str
    address: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True
