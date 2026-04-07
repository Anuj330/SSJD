from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from ..core.database import get_db
from ..core.security import verify_password
from ..core.jwt import create_access_token
from ..models.member_account import MemberAccount
from ..schemas.member_auth import MemberLoginRequest


def member_login(payload: MemberLoginRequest, db: Session = Depends(get_db)):
    account = (
        db.query(MemberAccount)
        .filter(MemberAccount.username == payload.username)
        .first()
    )

    if not account or not account.is_active:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(payload.password, account.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    account.last_login = datetime.utcnow()
    db.commit()

    token = create_access_token(
        {
            "sub": "member",
            "member_id": account.member_id,
        }
    )

    return {"access_token": token}
