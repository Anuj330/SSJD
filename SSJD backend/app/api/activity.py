"""Phase 5 — Activity log and receipt/voucher generation."""

from datetime import datetime
from decimal import Decimal

from fastapi import Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_admin, get_current_account
from app.models.activity_log import ActivityLog
from app.models.ledger import JournalEntry, JournalLine, Account


# ───────────────────────────────────
#  Activity Logging Helper
# ───────────────────────────────────

def log_activity(db, current, action, entity_type=None, entity_id=None, detail=None):
    """Call from other APIs to record activity."""
    entry = ActivityLog(
        user_role=current.role,
        user_sub=current.sub,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        detail=detail,
    )
    db.add(entry)


# ───────────────────────────────────
#  Activity Log API
# ───────────────────────────────────

def list_activity_logs(
    entity_type: str | None = Query(default=None),
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    q = db.query(ActivityLog).order_by(ActivityLog.created_at.desc())
    if entity_type:
        q = q.filter(ActivityLog.entity_type == entity_type)
    total = q.count()
    logs = q.offset(offset).limit(limit).all()
    return {
        "total": total,
        "logs": [
            {
                "id": log.id,
                "user_role": log.user_role,
                "user_sub": log.user_sub,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "detail": log.detail,
                "created_at": log.created_at,
            }
            for log in logs
        ],
    }


# ───────────────────────────────────
#  Receipt / Voucher Generation
# ───────────────────────────────────

def get_receipt(
    entry_id: int,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(get_current_account),
):
    """Generate a receipt/voucher for a journal entry."""
    entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(404, "Journal entry not found")

    lines = (
        db.query(JournalLine, Account)
        .join(Account, Account.id == JournalLine.account_id)
        .filter(JournalLine.journal_entry_id == entry_id)
        .all()
    )

    # RBAC: members can only view receipts for their own accounts
    if current.role == "member":
        member_involved = any(
            acct.owner_id == current.member_id and acct.owner_type.value == "member"
            for _, acct in lines
        )
        if not member_involved:
            raise HTTPException(403, "You can only view your own receipts")

    total_debit = Decimal("0")
    total_credit = Decimal("0")
    line_items = []
    for line, acct in lines:
        dr = Decimal(str(line.dr_amount))
        cr = Decimal(str(line.cr_amount))
        total_debit += dr
        total_credit += cr
        line_items.append({
            "account_code": acct.code,
            "account_name": acct.name,
            "debit": dr,
            "credit": cr,
            "note": line.line_note,
        })

    return {
        "receipt_no": entry.txn_ref,
        "date": entry.created_at,
        "txn_type": entry.txn_type,
        "description": entry.description,
        "status": entry.status.value if hasattr(entry.status, "value") else str(entry.status),
        "lines": line_items,
        "total_debit": total_debit,
        "total_credit": total_credit,
    }
