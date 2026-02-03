from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

from ..core.database import Base
from .base import TimestampMixin


class Member(Base, TimestampMixin):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    phone = Column(String, unique=True, index=True)
    address = Column(String, nullable=True)

    is_active = Column(Boolean, default=True)
