from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_admin, get_current_account
from app.models.member_profile import MemberProfile
from app.models.members import Member
from app.schemas.member_profile import (
    MemberProfileCreate,
    MemberProfileUpdate
)


def create_member_profile(
    payload: MemberProfileCreate,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(get_current_account),
):
    # Members can only create their own profile
    if current.role == "member":
        if payload.member_id and payload.member_id != current.member_id:
            raise HTTPException(status_code=403, detail="You can only create your own profile")
        payload_dict = payload.dict(exclude_unset=True)
        payload_dict["member_id"] = current.member_id
    else:
        payload_dict = payload.dict(exclude_unset=True)

    member = db.query(Member).filter(Member.id == payload_dict.get("member_id")).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    profile = MemberProfile(**payload_dict)

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def list_member_profiles(
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(get_current_account),
):
    # Members only see their own profile(s)
    if current.role == "member":
        return db.query(MemberProfile).filter(
            MemberProfile.member_id == current.member_id
        ).all()

    return db.query(MemberProfile).all()


def get_member_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(get_current_account),
):
    profile = db.query(MemberProfile).filter(MemberProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Member profile not found")

    # Members can only view their own profile
    if current.role == "member" and profile.member_id != current.member_id:
        raise HTTPException(status_code=403, detail="You can only view your own profile")

    return profile


def update_member_profile(
    profile_id: int,
    payload: MemberProfileUpdate,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(get_current_account),
):
    profile = db.query(MemberProfile).filter(MemberProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Member profile not found")

    # Members can only edit their own profile
    if current.role == "member" and profile.member_id != current.member_id:
        raise HTTPException(status_code=403, detail="You can only edit your own profile")

    for field, value in payload.dict(exclude_unset=True).items():
        # Members cannot change their member_id
        if current.role == "member" and field == "member_id":
            continue
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile
