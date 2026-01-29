from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password
from app.services.auth_service import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register")
def register_admin(
    society_id: int,
    name: str,
    email: str,
    password: str,
    db: Session = Depends(get_db)
):
    user = User(
        society_id=society_id,
        name=name,
        email=email,
        password_hash=hash_password(password),
        role="admin"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.email})
    return {"access_token": token}
