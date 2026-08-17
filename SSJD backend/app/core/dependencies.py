from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.jwt import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@dataclass
class CurrentUser:
    """Unified auth context returned by get_current_account."""
    role: str                   # "admin" or "member"
    sub: str                    # email (admin) or username (member)
    user_id: Optional[int] = None      # set for admins
    member_id: Optional[int] = None    # set for members


def get_current_account(
    token: str = Depends(oauth2_scheme),
) -> CurrentUser:
    """Decode JWT and return a CurrentUser. Raises 401 on bad/missing token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role = payload.get("role")
    sub = payload.get("sub")
    if not role or not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing required claims",
        )

    return CurrentUser(
        role=role,
        sub=sub,
        user_id=payload.get("user_id"),
        member_id=payload.get("member_id"),
    )


def require_admin(
    current: CurrentUser = Depends(get_current_account),
) -> CurrentUser:
    """Only allows admin users. Returns CurrentUser."""
    if current.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current


def require_member(
    current: CurrentUser = Depends(get_current_account),
) -> CurrentUser:
    """Only allows members. Returns CurrentUser with member_id."""
    if current.role != "member":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Member access required",
        )
    if not current.member_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing member_id",
        )
    return current
