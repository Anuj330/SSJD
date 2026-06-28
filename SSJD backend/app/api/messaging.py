"""SMS + WhatsApp messaging endpoints (admin only)."""

from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_admin, CurrentUser
from app.models.members import Member
from app.models.member_profile import MemberProfile
from app.models.member_account import MemberAccount
from app.services.notify_service import send_sms, send_whatsapp, provider_status


def _personalize(template, name=None, username=None, acno=None):
    """Substitute {name}, {username}, {acno} placeholders per recipient."""
    out = template or ""
    out = out.replace("{name}", name or "Member")
    out = out.replace("{username}", username or "")
    out = out.replace("{acno}", str(acno) if acno is not None else "")
    return out


def messaging_status(current: CurrentUser = Depends(require_admin)):
    return provider_status()


def list_contacts(db: Session = Depends(get_db), current: CurrentUser = Depends(require_admin)):
    """Members with a phone number (from member or profile)."""
    rows = (db.query(Member.id, Member.name, Member.phone, MemberProfile.phone_number,
                     MemberProfile.membership_number, MemberAccount.username)
            .outerjoin(MemberProfile, MemberProfile.member_id == Member.id)
            .outerjoin(MemberAccount, MemberAccount.member_id == Member.id)
            .filter(Member.is_active == True)  # noqa: E712
            .all())
    out = []
    for mid, name, phone, prof_phone, acno, username in rows:
        number = phone or prof_phone
        out.append({"id": mid, "name": name, "username": username, "phone": number,
                    "acno": acno, "has_phone": bool(number)})
    return out


def _send_one(channel, number, message):
    return (send_whatsapp if channel == "whatsapp" else send_sms)(number, message)


def send_message(
    member_id: int = Query(...),
    channel: str = Query(..., description="sms | whatsapp"),
    message: str = Query(...),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    if channel not in ("sms", "whatsapp"):
        raise HTTPException(400, "channel must be 'sms' or 'whatsapp'")
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(404, "Member not found")
    profile = db.query(MemberProfile).filter(MemberProfile.member_id == member_id).first()
    account = db.query(MemberAccount).filter(MemberAccount.member_id == member_id).first()
    number = member.phone or (profile.phone_number if profile else None)
    if not number:
        raise HTTPException(400, f"No phone number on file for {member.name}")
    body = _personalize(message, member.name, account.username if account else None,
                        profile.membership_number if profile else None)
    ok, detail = _send_one(channel, number, body)
    if not ok:
        raise HTTPException(502, f"Send failed: {detail}")
    return {"status": "sent", "channel": channel, "to": member.name, "detail": detail}


def send_bulk(
    channel: str = Query(..., description="sms | whatsapp"),
    message: str = Query(...),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    if channel not in ("sms", "whatsapp"):
        raise HTTPException(400, "channel must be 'sms' or 'whatsapp'")
    contacts = list_contacts(db, current)
    sent = failed = skipped = 0
    for c in contacts:
        if not c["has_phone"]:
            skipped += 1
            continue
        body = _personalize(message, c.get("name"), c.get("username"), c.get("acno"))
        ok, _ = _send_one(channel, c["phone"], body)
        sent += 1 if ok else 0
        failed += 0 if ok else 1
    return {"status": "completed", "channel": channel, "sent": sent, "failed": failed, "skipped_no_phone": skipped}
