from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func

from ..core.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_role = Column(String(20), nullable=False)
    user_sub = Column(String(120), nullable=False)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=True)   # member, loan, deposit, journal, etc.
    entity_id = Column(Integer, nullable=True)
    detail = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
