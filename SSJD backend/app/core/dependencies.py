from fastapi import Depends, HTTPException
from jose import jwt
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.jwt import SECRET_KEY, ALGORITHM
from ..models.member import Member


def get_current_member(token: str = Depends(...), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("sub") != "member":
            raise HTTPException(status_code=403, detail="Not a member")

        member_id = payload.get("member_id")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=401, detail="Member not found")

    return member
