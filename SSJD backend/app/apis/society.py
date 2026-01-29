from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.society import Society

router = APIRouter(prefix="/societies", tags=["Societies"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def create_society(name: str, registration_number: str, db: Session = Depends(get_db)):
    society = Society(
        name=name,
        registration_number=registration_number
    )
    db.add(society)
    db.commit()
    db.refresh(society)
    return society
