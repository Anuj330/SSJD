from datetime import datetime
from decimal import Decimal
import uuid

from fastapi import Depends, HTTPException, Query
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_admin, get_current_account
from app.models.ledger import Account, JournalEntry, JournalLine, EntryStatusEnum, OwnerTypeEnum
from app.schemas.ledger import AccountCreate, JournalPostRequest


def create_account(
    payload: AccountCreate,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    existing = db.query(Account).filter(Account.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Account code already exists")

    account = Account(
        code=payload.code,
        name=payload.name,
        type=payload.type,
        owner_type=payload.owner_type,
        owner_id=payload.owner_id,
        is_active=True,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def post_journal(
    payload: JournalPostRequest,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    if not payload.lines:
        raise HTTPException(status_code=400, detail="At least one journal line is required")

    total_debit = Decimal("0")
    total_credit = Decimal("0")

    account_ids = {line.account_id for line in payload.lines}
    found_count = db.query(Account).filter(Account.id.in_(account_ids)).count()
    if found_count != len(account_ids):
        raise HTTPException(status_code=400, detail="One or more accounts do not exist")

    for line in payload.lines:
        dr = Decimal(line.dr_amount)
        cr = Decimal(line.cr_amount)

        if dr < 0 or cr < 0:
            raise HTTPException(status_code=400, detail="Debit/Credit amounts cannot be negative")

        if (dr == 0 and cr == 0) or (dr > 0 and cr > 0):
            raise HTTPException(status_code=400, detail="Each line must have exactly one side: debit or credit")

        total_debit += dr
        total_credit += cr

    if total_debit != total_credit:
        raise HTTPException(status_code=400, detail="Journal entry is not balanced")

    txn_ref = payload.txn_ref or f"TXN-{uuid.uuid4().hex[:12].upper()}"

    existing_ref = db.query(JournalEntry).filter(JournalEntry.txn_ref == txn_ref).first()
    if existing_ref:
        raise HTTPException(status_code=409, detail="Duplicate txn_ref")

    entry = JournalEntry(
        txn_ref=txn_ref,
        txn_type=payload.txn_type,
        description=payload.description,
        created_by=payload.created_by or current.user_id,
        status=EntryStatusEnum.posted,
    )
    db.add(entry)
    db.flush()

    for line in payload.lines:
        db.add(
            JournalLine(
                journal_entry_id=entry.id,
                account_id=line.account_id,
                dr_amount=line.dr_amount,
                cr_amount=line.cr_amount,
                currency=line.currency,
                line_note=line.line_note,
            )
        )

    db.commit()
    db.refresh(entry)

    return {
        "id": entry.id,
        "txn_ref": entry.txn_ref,
        "status": entry.status.value,
        "total_debit": total_debit,
        "total_credit": total_credit,
    }


def reverse_journal(
    entry_id: int,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    if entry.status == EntryStatusEnum.reversed:
        raise HTTPException(status_code=400, detail="Entry already reversed")

    reverse_ref = f"REV-{entry.txn_ref}"
    if db.query(JournalEntry).filter(JournalEntry.txn_ref == reverse_ref).first():
        reverse_ref = f"REV-{entry.txn_ref}-{uuid.uuid4().hex[:6].upper()}"

    reversal = JournalEntry(
        txn_ref=reverse_ref,
        txn_type="reversal",
        description=f"Reversal of {entry.txn_ref}",
        created_by=current.user_id,
        status=EntryStatusEnum.posted,
        reversed_entry_id=entry.id,
    )
    db.add(reversal)
    db.flush()

    for line in entry.lines:
        db.add(
            JournalLine(
                journal_entry_id=reversal.id,
                account_id=line.account_id,
                dr_amount=line.cr_amount,
                cr_amount=line.dr_amount,
                currency=line.currency,
                line_note=f"Reversal line for {entry.txn_ref}",
            )
        )

    entry.status = EntryStatusEnum.reversed

    db.commit()
    return {"message": "Entry reversed", "reversal_entry_id": reversal.id, "reversal_txn_ref": reversal.txn_ref}


def account_statement(
    account_id: int,
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    query = (
        db.query(JournalLine, JournalEntry)
        .join(JournalEntry, JournalEntry.id == JournalLine.journal_entry_id)
        .filter(JournalLine.account_id == account_id)
    )

    if from_date:
        query = query.filter(JournalEntry.created_at >= from_date)
    if to_date:
        query = query.filter(JournalEntry.created_at <= to_date)

    rows = query.order_by(JournalEntry.created_at.asc()).all()

    result = []
    total_debit = Decimal("0")
    total_credit = Decimal("0")
    for line, entry in rows:
        total_debit += Decimal(line.dr_amount)
        total_credit += Decimal(line.cr_amount)
        result.append(
            {
                "entry_id": entry.id,
                "txn_ref": entry.txn_ref,
                "txn_type": entry.txn_type,
                "created_at": entry.created_at,
                "dr_amount": line.dr_amount,
                "cr_amount": line.cr_amount,
                "currency": line.currency,
                "line_note": line.line_note,
            }
        )

    return {
        "account_id": account.id,
        "account_code": account.code,
        "account_name": account.name,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "rows": result,
    }


def trial_balance(
    as_of: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    query = (
        db.query(
            Account.id.label("account_id"),
            Account.code.label("account_code"),
            Account.name.label("account_name"),
            Account.type.label("account_type"),
            func.coalesce(func.sum(JournalLine.dr_amount), 0).label("total_debit"),
            func.coalesce(func.sum(JournalLine.cr_amount), 0).label("total_credit"),
        )
        .join(JournalLine, JournalLine.account_id == Account.id)
        .join(JournalEntry, JournalEntry.id == JournalLine.journal_entry_id)
        .group_by(Account.id, Account.code, Account.name, Account.type)
        .order_by(Account.code.asc())
    )

    if as_of:
        query = query.filter(JournalEntry.created_at <= as_of)

    rows = query.all()

    total_debit = sum((Decimal(row.total_debit) for row in rows), Decimal("0"))
    total_credit = sum((Decimal(row.total_credit) for row in rows), Decimal("0"))

    return {
        "as_of": as_of,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "is_balanced": total_debit == total_credit,
        "rows": [
            {
                "account_id": row.account_id,
                "account_code": row.account_code,
                "account_name": row.account_name,
                "account_type": row.account_type.value if hasattr(row.account_type, "value") else str(row.account_type),
                "total_debit": row.total_debit,
                "total_credit": row.total_credit,
            }
            for row in rows
        ],
    }


def member_passbook(
    member_id: int,
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(get_current_account),
):
    """
    Full passbook view for a member — every transaction with running balance,
    penalty identification, and monthly summaries.
    """
    if current.role == "member" and current.member_id != member_id:
        raise HTTPException(status_code=403, detail="You can only view your own passbook")

    # Check member exists
    from app.models.members import Member
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    query = (
        db.query(JournalLine, JournalEntry, Account)
        .join(JournalEntry, JournalEntry.id == JournalLine.journal_entry_id)
        .join(Account, Account.id == JournalLine.account_id)
        .filter(
            and_(
                Account.owner_type == OwnerTypeEnum.member,
                Account.owner_id == member_id,
            )
        )
    )

    if from_date:
        query = query.filter(JournalEntry.created_at >= from_date)
    if to_date:
        query = query.filter(JournalEntry.created_at <= to_date)

    rows = query.order_by(JournalEntry.created_at.asc()).all()

    result = []
    running_balance = Decimal("0")
    total_credited = Decimal("0")
    total_debited = Decimal("0")
    total_penalty = Decimal("0")

    for line, entry, account in rows:
        dr = Decimal(line.dr_amount)
        cr = Decimal(line.cr_amount)
        total_credited += cr
        total_debited += dr
        running_balance += cr - dr

        # Identify penalty — check description for "(penalty:" pattern
        penalty_amount = Decimal("0")
        is_penalty = False
        desc = entry.description or ""
        if "penalty" in desc.lower():
            is_penalty = True
            # Try to extract penalty amount from description like "(penalty: 50.00)"
            import re
            match = re.search(r"penalty[:\s]+([\d,.]+)", desc, re.IGNORECASE)
            if match:
                try:
                    penalty_amount = Decimal(match.group(1).replace(",", ""))
                except Exception:
                    pass
            total_penalty += penalty_amount

        result.append({
            "date": entry.created_at,
            "txn_ref": entry.txn_ref,
            "txn_type": entry.txn_type,
            "description": desc,
            "account_name": account.name,
            "debit": dr,
            "credit": cr,
            "penalty": penalty_amount,
            "is_penalty": is_penalty,
            "running_balance": running_balance,
        })

    # Monthly summary
    monthly = {}
    for row in result:
        key = row["date"].strftime("%Y-%m") if row["date"] else "unknown"
        if key not in monthly:
            monthly[key] = {"month": key, "total_credit": Decimal("0"), "total_debit": Decimal("0"), "penalty": Decimal("0"), "txn_count": 0}
        monthly[key]["total_credit"] += row["credit"]
        monthly[key]["total_debit"] += row["debit"]
        monthly[key]["penalty"] += row["penalty"]
        monthly[key]["txn_count"] += 1

    monthly_summary = sorted(monthly.values(), key=lambda x: x["month"])

    return {
        "member_id": member_id,
        "member_name": member.name,
        "total_credited": total_credited,
        "total_debited": total_debited,
        "total_penalty": total_penalty,
        "current_balance": running_balance,
        "transaction_count": len(result),
        "rows": result,
        "monthly_summary": monthly_summary,
    }


def member_money_flow(
    member_id: int,
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(get_current_account),
):
    # Members can only view their own money flow
    if current.role == "member" and current.member_id != member_id:
        raise HTTPException(status_code=403, detail="You can only view your own money flow")

    query = (
        db.query(JournalLine, JournalEntry, Account)
        .join(JournalEntry, JournalEntry.id == JournalLine.journal_entry_id)
        .join(Account, Account.id == JournalLine.account_id)
        .filter(
            and_(
                Account.owner_type == OwnerTypeEnum.member,
                Account.owner_id == member_id,
            )
        )
    )

    if from_date:
        query = query.filter(JournalEntry.created_at >= from_date)
    if to_date:
        query = query.filter(JournalEntry.created_at <= to_date)

    rows = query.order_by(JournalEntry.created_at.asc()).all()

    result = []
    total_debit = Decimal("0")
    total_credit = Decimal("0")
    for line, entry, account in rows:
        total_debit += Decimal(line.dr_amount)
        total_credit += Decimal(line.cr_amount)
        result.append(
            {
                "entry_id": entry.id,
                "txn_ref": entry.txn_ref,
                "txn_type": entry.txn_type,
                "created_at": entry.created_at,
                "account_code": account.code,
                "account_name": account.name,
                "dr_amount": line.dr_amount,
                "cr_amount": line.cr_amount,
            }
        )

    return {
        "member_id": member_id,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "net_credit_minus_debit": total_credit - total_debit,
        "rows": result,
    }
