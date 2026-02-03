from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date
from enum import Enum

class GenderEnum(str, Enum):
    male = "male"
    female = "female"
    other = "other"

class MemberProfileCreate(BaseModel):
    member_id: Optional[int] = None

    name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None 
    membership_number: Optional[int] = None
    date_of_joining: Optional[date] = None

    address: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None

    aadhar: Optional[str] = None
    pan: Optional[str] = None

    bank_name: Optional[str] = None
    account_number: Optional[int] = None
    ifsc: Optional[str] = None

    nominee1: Optional[str] = None
    nominee1_dob: Optional[date] = None
    nominee1_relation: Optional[str] = None

    nominee2: Optional[str] = None
    nominee2_dob: Optional[date] = None
    nominee2_relation: Optional[str] = None


class MemberProfileUpdate(MemberProfileCreate):
    pass  # same fields, all optional


class MemberProfileResponse(MemberProfileCreate):
    id: int

    class Config:
        from_attributes = True
