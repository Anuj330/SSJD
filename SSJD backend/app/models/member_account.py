from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


class MemberAccount(Base):
    __tablename__ = "member_accounts"

    id = Column(Integer, primary_key=True, index=True)

    member_id = Column(Integer, ForeignKey("members.id"), unique=True, nullable=False)
    member = relationship("Member")

    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
