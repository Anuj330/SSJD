"""Aadhaar intake, name-matching, and review/approval workflow (admin only)."""

import os
import re
import hashlib
import uuid
from datetime import datetime, date
from difflib import SequenceMatcher

from fastapi import Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_admin
from app.models.members import Member
from app.models.member_profile import MemberProfile
from app.models.aadhaar import (
    AadhaarDocument, AadhaarAuditLog,
    AADHAAR_PENDING, AADHAAR_PENDING_APPROVAL, AADHAAR_LINKED,
    AADHAAR_NEEDS_INFO, AADHAAR_REJECTED,
)

AADHAAR_DIR = os.getenv("AADHAAR_DIR", "/data/aadhaar")
ALLOWED_MIME = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "application/pdf": "pdf"}

# Honorifics / relationship prefixes stripped purely for name comparison.
_NOISE = re.compile(
    r"\b(mr|mrs|ms|smt|shri|sri|sm|km|kumari|kum|dr|m/s|w/o|s/o|d/o|c/o)\b\.?",
    re.IGNORECASE,
)


def normalize_name(name: str) -> str:
    s = (name or "").lower()
    s = re.sub(r"\(.*?\)", " ", s)        # drop the (account-code) suffix in member names
    s = _NOISE.sub(" ", s)
    s = re.sub(r"[^a-z\s]", " ", s)       # drop digits/punctuation
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _token_sorted(s: str) -> str:
    return " ".join(sorted(s.split()))


def _audit(db, doc_id, action, actor, detail=None):
    db.add(AadhaarAuditLog(document_id=doc_id, action=action, actor=actor, detail=detail))


def _hash_number(num: str) -> str:
    return hashlib.sha256(num.encode("utf-8")).hexdigest()


def find_candidates(db: Session, confirmed_name: str, limit: int = 20):
    """Rank member profiles by normalized-name similarity. Name is the only key;
    other attributes are returned for human disambiguation, not matching."""
    target = normalize_name(confirmed_name)
    target_sorted = _token_sorted(target)
    rows = (db.query(MemberProfile, Member.phone)
            .join(Member, Member.id == MemberProfile.member_id)
            .all())
    scored = []
    exact = 0
    for profile, phone in rows:
        norm = normalize_name(profile.name or "")
        if not norm:
            continue
        if norm == target and target:
            score = 100
            exact += 1
        else:
            score = round(SequenceMatcher(None, target_sorted, _token_sorted(norm)).ratio() * 100)
        if score >= 60:
            scored.append({
                "member_id": profile.member_id,
                "name": profile.name,
                "acno": profile.membership_number,
                "father_name": profile.father_name,
                "phone": phone or profile.phone_number,
                "date_of_joining": str(profile.date_of_joining) if profile.date_of_joining else None,
                "score": score,
            })
    scored.sort(key=lambda c: c["score"], reverse=True)

    if exact > 1:
        confidence = "ambiguous"   # duplicate names — must be resolved manually
    elif exact == 1:
        confidence = "high"        # unique exact name — still confirmed by a human
    elif scored:
        confidence = "fuzzy"       # only near matches — needs review
    else:
        confidence = "none"        # no candidate member
    return scored[:limit], confidence


def _doc_dict(doc: AadhaarDocument):
    return {
        "id": doc.id, "status": doc.status, "confirmed_name": doc.confirmed_name,
        "aadhaar_last4": doc.aadhaar_last4, "dob": str(doc.dob) if doc.dob else None,
        "match_confidence": doc.match_confidence, "member_id": doc.member_id,
        "link_basis": doc.link_basis, "remarks": doc.remarks,
        "uploaded_by": doc.uploaded_by, "decided_by": doc.decided_by, "approved_by": doc.approved_by,
        "has_image": bool(doc.image_path),
        "linked_at": str(doc.linked_at) if doc.linked_at else None,
        "created_at": str(doc.created_at) if doc.created_at else None,
    }


# ─────────────────────────── endpoints ───────────────────────────

async def upload_aadhaar(
    name: str = Form(...),
    aadhaar_number: str = Form(...),
    dob: str = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    name = (name or "").strip()
    if not name:
        raise HTTPException(400, "Confirmed name is required")

    digits = re.sub(r"\D", "", aadhaar_number or "")
    if len(digits) != 12:
        raise HTTPException(400, "Aadhaar number must be 12 digits")

    mime = file.content_type
    if mime not in ALLOWED_MIME:
        raise HTTPException(400, "Unsupported file type (use JPG/PNG/WEBP/PDF)")

    a_hash = _hash_number(digits)
    if db.query(AadhaarDocument).filter(AadhaarDocument.aadhaar_hash == a_hash).first():
        raise HTTPException(409, "This Aadhaar number is already on file")

    # Store the image on the restricted volume.
    os.makedirs(AADHAAR_DIR, exist_ok=True)
    ext = ALLOWED_MIME[mime]
    fname = f"aadhaar_{uuid.uuid4().hex}.{ext}"
    fpath = os.path.join(AADHAAR_DIR, fname)
    content = await file.read()
    if len(content) > 8 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 8 MB)")
    with open(fpath, "wb") as f:
        f.write(content)

    parsed_dob = None
    if dob:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                parsed_dob = datetime.strptime(dob.strip(), fmt).date()
                break
            except ValueError:
                continue

    _, confidence = find_candidates(db, name)

    doc = AadhaarDocument(
        status=AADHAAR_PENDING, confirmed_name=name,
        aadhaar_hash=a_hash, aadhaar_last4=digits[-4:], dob=parsed_dob,
        image_path=fpath, image_mime=mime, match_confidence=confidence,
        uploaded_by=current.user_id,
    )
    db.add(doc)
    db.flush()
    _audit(db, doc.id, "uploaded", current.user_id, f"name='{name}', confidence={confidence}")
    db.commit()
    return {**_doc_dict(doc), "message": "Uploaded — pending review"}


def list_aadhaar(status: str = Query(default=None), db: Session = Depends(get_db),
                 current: CurrentUser = Depends(require_admin)):
    q = db.query(AadhaarDocument)
    if status:
        q = q.filter(AadhaarDocument.status == status)
    docs = q.order_by(AadhaarDocument.id.desc()).all()
    return {"count": len(docs), "documents": [_doc_dict(d) for d in docs]}


def get_aadhaar(doc_id: int, db: Session = Depends(get_db),
                current: CurrentUser = Depends(require_admin)):
    doc = db.query(AadhaarDocument).filter(AadhaarDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    candidates, _ = find_candidates(db, doc.confirmed_name)
    audit = (db.query(AadhaarAuditLog).filter(AadhaarAuditLog.document_id == doc_id)
             .order_by(AadhaarAuditLog.id).all())
    linked_member = None
    if doc.member_id:
        m = db.query(MemberProfile).filter(MemberProfile.member_id == doc.member_id).first()
        if m:
            linked_member = {"member_id": m.member_id, "name": m.name, "acno": m.membership_number}
    return {
        **_doc_dict(doc),
        "candidates": candidates,
        "linked_member": linked_member,
        "audit": [{"action": a.action, "actor": a.actor, "detail": a.detail,
                   "at": str(a.created_at) if a.created_at else None} for a in audit],
    }


def get_aadhaar_image(doc_id: int, db: Session = Depends(get_db),
                      current: CurrentUser = Depends(require_admin)):
    doc = db.query(AadhaarDocument).filter(AadhaarDocument.id == doc_id).first()
    if not doc or not doc.image_path or not os.path.exists(doc.image_path):
        raise HTTPException(404, "Image not found")
    return FileResponse(doc.image_path, media_type=doc.image_mime or "application/octet-stream")


def link_aadhaar(doc_id: int, member_id: int = Query(...), basis: str = Query(default=""),
                 db: Session = Depends(get_db), current: CurrentUser = Depends(require_admin)):
    doc = db.query(AadhaarDocument).filter(AadhaarDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc.status in (AADHAAR_LINKED,):
        raise HTTPException(400, "Already linked")

    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(404, "Member not found")

    # one Aadhaar per member
    other = (db.query(AadhaarDocument)
             .filter(AadhaarDocument.member_id == member_id, AadhaarDocument.id != doc_id,
                     AadhaarDocument.status.in_([AADHAAR_LINKED, AADHAAR_PENDING_APPROVAL]))
             .first())
    if other:
        raise HTTPException(409, "This member already has an Aadhaar on file")

    doc.member_id = member_id
    doc.link_basis = basis.strip() or None
    doc.decided_by = current.user_id
    # High-confidence unique match → operator may finalize; otherwise needs a checker.
    if doc.match_confidence == "high":
        doc.status = AADHAAR_LINKED
        doc.linked_at = datetime.utcnow()
        _audit(db, doc.id, "linked", current.user_id, f"member_id={member_id}; basis={basis}")
    else:
        doc.status = AADHAAR_PENDING_APPROVAL
        _audit(db, doc.id, "link_proposed", current.user_id,
               f"member_id={member_id}; confidence={doc.match_confidence}; basis={basis}")
    db.commit()
    return _doc_dict(doc)


def approve_aadhaar(doc_id: int, db: Session = Depends(get_db),
                    current: CurrentUser = Depends(require_admin)):
    doc = db.query(AadhaarDocument).filter(AadhaarDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc.status != AADHAAR_PENDING_APPROVAL:
        raise HTTPException(400, "Not awaiting approval")

    doc.status = AADHAAR_LINKED
    doc.approved_by = current.user_id
    doc.linked_at = datetime.utcnow()
    same = doc.approved_by == doc.decided_by
    _audit(db, doc.id, "approved", current.user_id,
           f"member_id={doc.member_id}" + (" [maker==checker]" if same else ""))
    db.commit()
    return _doc_dict(doc)


def reject_aadhaar(doc_id: int, remarks: str = Query(default=""), db: Session = Depends(get_db),
                   current: CurrentUser = Depends(require_admin)):
    doc = db.query(AadhaarDocument).filter(AadhaarDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    doc.status = AADHAAR_REJECTED
    doc.member_id = None
    doc.remarks = remarks.strip() or None
    doc.decided_by = current.user_id
    _audit(db, doc.id, "rejected", current.user_id, remarks)
    db.commit()
    return _doc_dict(doc)


def defer_aadhaar(doc_id: int, remarks: str = Query(default=""), db: Session = Depends(get_db),
                  current: CurrentUser = Depends(require_admin)):
    doc = db.query(AadhaarDocument).filter(AadhaarDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    doc.status = AADHAAR_NEEDS_INFO
    doc.remarks = remarks.strip() or None
    _audit(db, doc.id, "deferred", current.user_id, remarks)
    db.commit()
    return _doc_dict(doc)


def unlink_aadhaar(doc_id: int, db: Session = Depends(get_db),
                   current: CurrentUser = Depends(require_admin)):
    doc = db.query(AadhaarDocument).filter(AadhaarDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    prev = doc.member_id
    doc.status = AADHAAR_PENDING
    doc.member_id = None
    doc.approved_by = None
    doc.linked_at = None
    _audit(db, doc.id, "unlinked", current.user_id, f"was member_id={prev}")
    db.commit()
    return _doc_dict(doc)
