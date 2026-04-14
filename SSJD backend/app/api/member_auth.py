from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.security import verify_password, hash_password
from app.core.jwt import create_access_token
from app.core.dependencies import CurrentUser, require_admin
from app.models.member_account import MemberAccount
from app.models.members import Member
from app.schemas.member_auth import MemberLoginRequest, MemberRegisterRequest


def member_register(
    payload: MemberRegisterRequest,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    member = db.query(Member).filter(Member.id == payload.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    existing = db.query(MemberAccount).filter(
        (MemberAccount.member_id == payload.member_id) |
        (MemberAccount.username == payload.username)
    ).first()
    if existing:
        if existing.member_id == payload.member_id:
            raise HTTPException(status_code=400, detail="Member already has an account")
        raise HTTPException(status_code=400, detail="Username already taken")

    account = MemberAccount(
        member_id=payload.member_id,
        username=payload.username,
        password_hash=hash_password(payload.password),
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    return {
        "id": account.id,
        "member_id": account.member_id,
        "username": account.username,
        "is_active": account.is_active,
    }


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
            "sub": account.username,
            "role": "member",
            "member_id": account.member_id,
        }
    )

    return {"access_token": token, "token_type": "bearer"}
