from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.user import UserCreate, UserResponse
from app.models.user import User
from app.core.database import get_db
from app.core.security import hash_password
from app.core.dependencies import CurrentUser, require_admin

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists"
        )

    user = User(
        society_id=payload.society_id,
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user
