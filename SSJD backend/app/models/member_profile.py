from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    DateTime,
    ForeignKey,
    BigInteger,
    Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from ..core.database import Base
from .base import TimestampMixin


class GenderEnum(enum.Enum):
    male = "male"
    female = "female"
    other = "other"


class MemberProfile(Base, TimestampMixin):
    __tablename__ = "member_profiles"

    id = Column(Integer, primary_key=True, index=True)

    # 🔑 CORRECT RELATIONSHIP
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    member = relationship("Member")

    # 🧾 Optional audit field (staff who created/updated)
    # created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # created_by = relationship("User")

    # --- Personal Info ---
    name = Column(String(100), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(Enum(GenderEnum, name="genderenum"), nullable=True)
    membership_number = Column(Integer, nullable=True)
    date_of_joining = Column(Date, nullable=True)

    # --- Contact ---
    address = Column(Text, nullable=True)
    email = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)

    # --- KYC ---
    aadhar = Column(String(20), nullable=True)
    pan = Column(String(20), nullable=True)

    # --- Bank ---
    bank_name = Column(String(100), nullable=True)
    account_number = Column(BigInteger, nullable=True)
    ifsc = Column(String(20), nullable=True)

    # --- Nominee 1 ---
    nominee1 = Column(String(100), nullable=True)
    nominee1_dob = Column(Date, nullable=True)
    nominee1_relation = Column(String(100), nullable=True)

    # --- Nominee 2 ---
    nominee2 = Column(String(100), nullable=True)
    nominee2_dob = Column(Date, nullable=True)
    nominee2_relation = Column(String(100), nullable=True)

    # --- Timestamps ---
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
