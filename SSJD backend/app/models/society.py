from sqlalchemy import Column, Integer, String
from core.database import Base
from models.base import TimestampMixin

class Society(Base, TimestampMixin):
    __tablename__ = "societies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    registration_number = Column(String, unique=True)
    state = Column(String)
    status = Column(String, default="active")
    address = Column(String)
