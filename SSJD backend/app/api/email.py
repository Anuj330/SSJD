"""Email notification endpoints — admin only."""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_admin, CurrentUser
from app.models.members import Member
from app.models.member_profile import MemberProfile
from app.services.email_service import send_email


async def list_members_with_email(
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    """Return all members with their email from profile (if available)."""
    members = db.query(Member).filter(Member.is_active == True).all()

    result = []
    for m in members:
        profile = db.query(MemberProfile).filter(MemberProfile.member_id == m.id).first()
        result.append({
            "id": m.id,
            "name": m.name,
            "phone": m.phone,
            "email": profile.email if profile and profile.email else None,
            "has_profile": profile is not None,
        })

    return result


async def send_notification(
    member_id: int,
    subject: str,
    message: str,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    """Send a custom email notification to a member."""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    profile = db.query(MemberProfile).filter(MemberProfile.member_id == member_id).first()
    if not profile or not profile.email:
        raise HTTPException(
            status_code=400,
            detail=f"No email address found for member {member.name}. Please update their profile first.",
        )

    html_body = f"""<h2>Dear {member.name},</h2>
    <div>{message.replace(chr(10), '<br>')}</div>
    <br><p>— SSJD Cooperative Society</p>"""

    success = send_email(profile.email, member.name, subject, html_body)

    if not success:
        raise HTTPException(
            status_code=503,
            detail="Email service unavailable. Check Brevo API key configuration.",
        )

    return {
        "status": "sent",
        "to_email": profile.email,
        "to_name": member.name,
        "subject": subject,
    }


async def send_bulk_notification(
    subject: str,
    message: str,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    """Send a notification to ALL members who have email addresses."""
    profiles = (
        db.query(MemberProfile, Member)
        .join(Member, MemberProfile.member_id == Member.id)
        .filter(Member.is_active == True, MemberProfile.email.isnot(None), MemberProfile.email != "")
        .all()
    )

    if not profiles:
        raise HTTPException(status_code=400, detail="No members with email addresses found.")

    html_body_template = """<h2>Dear {name},</h2>
    <div>{message}</div>
    <br><p>— SSJD Cooperative Society</p>"""

    sent = 0
    failed = 0
    for profile, member in profiles:
        html = html_body_template.format(name=member.name, message=message.replace("\n", "<br>"))
        ok = send_email(profile.email, member.name, subject, html)
        if ok:
            sent += 1
        else:
            failed += 1

    return {
        "status": "completed",
        "total_recipients": len(profiles),
        "sent": sent,
        "failed": failed,
    }
