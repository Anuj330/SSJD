from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_admin, get_current_account
from app.models.members import Member
from app.schemas.members import MemberCreate, MemberUpdate


def create_member(
    payload: MemberCreate,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    existing = db.query(Member).filter(Member.phone == payload.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="Member with this phone already exists")

    member = Member(
        name=payload.name,
        phone=payload.phone,
        address=payload.address
    )

    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def list_members(
    status: str = Query(default="active", description="active | inactive | all"),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    q = db.query(Member)
    if status == "active":
        q = q.filter(Member.is_active == True)  # noqa: E712
    elif status == "inactive":
        q = q.filter(Member.is_active == False)  # noqa: E712
    members = q.order_by(Member.id).all()
    return {"count": len(members), "members": members}


def get_member(
    member_id: int,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(get_current_account),
):
    # Members can only view themselves
    if current.role == "member" and current.member_id != member_id:
        raise HTTPException(status_code=403, detail="You can only view your own data")

    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


def update_member(
    member_id: int,
    payload: MemberUpdate,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(member, field, value)

    db.commit()
    db.refresh(member)
    return member


def deactivate_member(
    member_id: int,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    member.is_active = False
    db.commit()
    return {"message": "Member deactivated"}


def reactivate_member(
    member_id: int,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.is_active = True
    db.commit()
    return {"message": "Member reactivated"}
