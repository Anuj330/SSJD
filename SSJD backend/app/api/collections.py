"""Unified cash collection — split one payment across loan EMI, share money,
and the member's advance (adjust-balance) wallet, atomically."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_admin
from app.models.members import Member
from app.models.member_profile import MemberProfile
from app.models.loan import LoanAccount, LoanStatusEnum
from app.models.ledger import AccountTypeEnum
from app.models.advance import (
    MemberAdvance, AdvanceTransaction, ADVANCE_CREDIT, gen_advance_txn_id,
)
from app.api.shares import deposit_share, _get_or_create_account, _post_journal, CASH_CODE
from app.api.loans import apply_repayment

ADVANCE_CODE = "MEMBER-ADV-001"


def _parse_date(s):
    if s:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(s.strip(), fmt).date()
            except ValueError:
                continue
    return date.today()


def credit_advance(db, member, amount, d, remarks, created_by, reference="Collection"):
    """Park money in a member's advance wallet (no commit). Dr Cash, Cr Member Advance."""
    wallet = db.query(MemberAdvance).filter(MemberAdvance.member_id == member.id).first()
    if not wallet:
        wallet = MemberAdvance(member_id=member.id, balance=Decimal("0"))
        db.add(wallet)
        db.flush()
    adv_acct = _get_or_create_account(db, ADVANCE_CODE, "Member Advance (Wallet)", AccountTypeEnum.liability)
    cash = _get_or_create_account(db, CASH_CODE, "Cash / Bank", AccountTypeEnum.asset)
    entry = _post_journal(db, "advance_credit", f"Advance held for {member.name}",
                          cash.id, adv_acct.id, amount, created_by)
    wallet.balance += amount
    txn_id = gen_advance_txn_id()
    db.add(AdvanceTransaction(
        transaction_id=txn_id, member_id=member.id, txn_type=ADVANCE_CREDIT,
        amount=amount, txn_date=d, reference=reference,
        journal_entry_id=entry.id, remarks=remarks or None))
    return txn_id, wallet


class CollectRequest(BaseModel):
    total: Decimal = Field(gt=0)
    loan_id: Optional[int] = None
    loan_amount: Decimal = Field(default=Decimal("0"), ge=0)
    share_amount: Decimal = Field(default=Decimal("0"), ge=0)
    share_cd: Optional[Decimal] = None   # Compulsory Deposit portion of the share amount
    share_od: Optional[Decimal] = None   # Optional Deposit portion of the share amount
    advance_amount: Decimal = Field(default=Decimal("0"), ge=0)
    txn_date: Optional[str] = None
    remarks: Optional[str] = None


def collect_payment(member_id: int, payload: CollectRequest,
                    db: Session = Depends(get_db),
                    current: CurrentUser = Depends(require_admin)):
    """Record one collection from a member and split it across loan / share / advance.
    All three post in a single transaction — either everything commits or nothing."""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(404, "Member not found")

    alloc = payload.loan_amount + payload.share_amount + payload.advance_amount
    if alloc != payload.total:
        raise HTTPException(400, f"Allocations (Rs {alloc}) must equal total received (Rs {payload.total})")
    if alloc <= 0:
        raise HTTPException(400, "Nothing allocated")

    d = _parse_date(payload.txn_date)
    result = {"member_id": member_id, "total": payload.total, "date": d.isoformat(),
              "loan": None, "share": None, "advance": None}

    if payload.loan_amount > 0:
        if not payload.loan_id:
            raise HTTPException(400, "loan_id is required when allocating to a loan")
        loan = (db.query(LoanAccount)
                .filter(LoanAccount.id == payload.loan_id, LoanAccount.member_id == member_id)
                .first())
        if not loan:
            raise HTTPException(404, "Loan not found for this member")
        if loan.status != LoanStatusEnum.active:
            raise HTTPException(400, "Loan is not active")
        result["loan"] = apply_repayment(db, loan, payload.loan_amount, d,
                                         payload.remarks, current.user_id)

    if payload.share_amount > 0:
        ref_month = date(d.year, d.month, 1)
        txn_id, holding, _amt = deposit_share(db, member, payload.share_amount, d, ref_month,
                                              payload.remarks, current.user_id,
                                              cd_amount=payload.share_cd, od_amount=payload.share_od)
        result["share"] = {"transaction_id": txn_id, "balance": holding.balance,
                           "cd_balance": holding.cd_balance, "od_balance": holding.od_balance}

    if payload.advance_amount > 0:
        txn_id, wallet = credit_advance(db, member, payload.advance_amount, d,
                                        payload.remarks, current.user_id)
        result["advance"] = {"transaction_id": txn_id, "balance": wallet.balance}

    db.commit()
    _notify_collection(db, member, payload)
    return result


def _notify_collection(db, member, payload):
    try:
        from app.services.notify_service import send_whatsapp
        prof = db.query(MemberProfile).filter(MemberProfile.member_id == member.id).first()
        phone = member.phone or (prof.phone_number if prof else None)
        if not phone:
            return
        parts = []
        if payload.loan_amount > 0:
            parts.append(f"EMI Rs {payload.loan_amount}")
        if payload.share_amount > 0:
            parts.append(f"share Rs {payload.share_amount}")
        if payload.advance_amount > 0:
            parts.append(f"advance Rs {payload.advance_amount}")
        send_whatsapp(phone, f"Hi {member.name}, SSJD Cooperative received Rs {payload.total} "
                             f"({', '.join(parts)}). Thank you.")
    except Exception:
        pass


def get_member_advance(member_id: int, db: Session = Depends(get_db),
                       current: CurrentUser = Depends(require_admin)):
    """Advance-wallet balance + history for a member."""
    wallet = db.query(MemberAdvance).filter(MemberAdvance.member_id == member_id).first()
    txns = (db.query(AdvanceTransaction)
            .filter(AdvanceTransaction.member_id == member_id)
            .order_by(AdvanceTransaction.id.desc()).all())
    return {
        "member_id": member_id,
        "balance": wallet.balance if wallet else 0,
        "transactions": [
            {"transaction_id": t.transaction_id, "txn_type": t.txn_type, "amount": t.amount,
             "txn_date": t.txn_date, "reference": t.reference, "remarks": t.remarks}
            for t in txns
        ],
    }
