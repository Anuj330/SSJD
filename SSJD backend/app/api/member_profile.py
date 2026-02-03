from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.member_profile import MemberProfile
from ..models.members import Member
from ..schemas.member_profile import (
    MemberProfileCreate,
    MemberProfileUpdate
)


def create_member_profile(
    payload: MemberProfileCreate,
    db: Session = Depends(get_db)
):
    member = db.query(Member).filter(Member.id == payload.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    profile = MemberProfile(**payload.dict(exclude_unset=True))

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def list_member_profiles(db: Session = Depends(get_db)):
    return db.query(MemberProfile).all()


def get_member_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.query(MemberProfile).filter(MemberProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Member profile not found")
    return profile


def update_member_profile(
    profile_id: int,
    payload: MemberProfileUpdate,
    db: Session = Depends(get_db)
):
    profile = db.query(MemberProfile).filter(MemberProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Member profile not found")

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile
