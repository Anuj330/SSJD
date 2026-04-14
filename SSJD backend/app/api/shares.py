from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import uuid

from dateutil.relativedelta import relativedelta
from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_admin, get_current_account
from app.models.share import ShareHolding, ShareTransaction, ShareTransactionTypeEnum, RDInstallment
from app.models.deposit import DepositAccount, DepositStatusEnum
from app.models.scheme import Scheme, SchemeTypeEnum
from app.models.ledger import (
    Account, JournalEntry, JournalLine,
    AccountTypeEnum, OwnerTypeEnum, EntryStatusEnum,
)
from app.models.members import Member


CASH_CODE = "CASH-001"
SHARE_CAPITAL_CODE = "SHARE-CAP-001"


def _get_or_create_account(db, code, name, acct_type):
    acct = db.query(Account).filter(Account.code == code).first()
    if not acct:
        acct = Account(code=code, name=name, type=acct_type,
                       owner_type=OwnerTypeEnum.society, is_active=True)
        db.add(acct)
        db.flush()
    return acct


def _post_journal(db, txn_type, description, dr_id, cr_id, amount, created_by):
    txn_ref = f"TXN-{uuid.uuid4().hex[:12].upper()}"
    entry = JournalEntry(txn_ref=txn_ref, txn_type=txn_type, description=description,
                         created_by=created_by, status=EntryStatusEnum.posted)
    db.add(entry)
    db.flush()
    db.add(JournalLine(journal_entry_id=entry.id, account_id=dr_id,
                        dr_amount=amount, cr_amount=Decimal("0")))
    db.add(JournalLine(journal_entry_id=entry.id, account_id=cr_id,
                        dr_amount=Decimal("0"), cr_amount=amount))
    return entry


# ───────────────────────────────────
#  Share Capital
# ───────────────────────────────────

def purchase_shares(member_id: int, shares: int = Query(gt=0),
                    face_value: Decimal = Query(default=Decimal("10")),
                    db: Session = Depends(get_db),
                    current: CurrentUser = Depends(require_admin)):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(404, "Member not found")

    amount = Decimal(str(shares)) * face_value

    holding = db.query(ShareHolding).filter(ShareHolding.member_id == member_id).first()
    if not holding:
        holding = ShareHolding(member_id=member_id, face_value_per_share=face_value)
        db.add(holding)
        db.flush()

    # Journal: Dr Cash, Cr Share Capital (equity)
    cash = _get_or_create_account(db, CASH_CODE, "Cash / Bank", AccountTypeEnum.asset)
    share_cap = _get_or_create_account(db, SHARE_CAPITAL_CODE, "Share Capital", AccountTypeEnum.equity)
    entry = _post_journal(db, "share_purchase",
                          f"Share purchase by {member.name} ({shares} shares)",
                          cash.id, share_cap.id, amount, current.user_id)

    holding.total_shares += shares
    holding.total_value += amount

    db.add(ShareTransaction(
        member_id=member_id, txn_type=ShareTransactionTypeEnum.purchase,
        shares=shares, amount=amount, txn_date=date.today(),
        journal_entry_id=entry.id,
    ))

    db.commit()
    return {"message": f"{shares} shares purchased", "total_shares": holding.total_shares,
            "total_value": holding.total_value}


def refund_shares(member_id: int, shares: int = Query(gt=0),
                  db: Session = Depends(get_db),
                  current: CurrentUser = Depends(require_admin)):
    holding = db.query(ShareHolding).filter(ShareHolding.member_id == member_id).first()
    if not holding or holding.total_shares < shares:
        raise HTTPException(400, "Insufficient shares")

    member = db.query(Member).filter(Member.id == member_id).first()
    amount = Decimal(str(shares)) * holding.face_value_per_share

    cash = _get_or_create_account(db, CASH_CODE, "Cash / Bank", AccountTypeEnum.asset)
    share_cap = _get_or_create_account(db, SHARE_CAPITAL_CODE, "Share Capital", AccountTypeEnum.equity)
    entry = _post_journal(db, "share_refund",
                          f"Share refund for {member.name} ({shares} shares)",
                          share_cap.id, cash.id, amount, current.user_id)

    holding.total_shares -= shares
    holding.total_value -= amount

    db.add(ShareTransaction(
        member_id=member_id, txn_type=ShareTransactionTypeEnum.refund,
        shares=-shares, amount=amount, txn_date=date.today(),
        journal_entry_id=entry.id,
    ))

    db.commit()
    return {"message": f"{shares} shares refunded", "total_shares": holding.total_shares}


def get_member_shares(member_id: int, db: Session = Depends(get_db),
                      current: CurrentUser = Depends(get_current_account)):
    if current.role == "member" and current.member_id != member_id:
        raise HTTPException(403, "You can only view your own shares")

    holding = db.query(ShareHolding).filter(ShareHolding.member_id == member_id).first()
    txns = (db.query(ShareTransaction)
            .filter(ShareTransaction.member_id == member_id)
            .order_by(ShareTransaction.txn_date.desc()).all())

    return {
        "member_id": member_id,
        "total_shares": holding.total_shares if holding else 0,
        "face_value_per_share": holding.face_value_per_share if holding else 10,
        "total_value": holding.total_value if holding else 0,
        "transactions": [
            {"id": t.id, "txn_type": t.txn_type.value, "shares": t.shares,
             "amount": t.amount, "txn_date": t.txn_date, "remarks": t.remarks}
            for t in txns
        ],
    }


def list_all_shares(db: Session = Depends(get_db),
                    current: CurrentUser = Depends(require_admin)):
    holdings = (db.query(ShareHolding, Member.name)
                .join(Member, Member.id == ShareHolding.member_id)
                .order_by(ShareHolding.member_id).all())
    return [
        {"member_id": h.member_id, "member_name": name,
         "total_shares": h.total_shares, "total_value": h.total_value,
         "face_value_per_share": h.face_value_per_share}
        for h, name in holdings
    ]


# ───────────────────────────────────
#  RD Installment Tracking
# ───────────────────────────────────

def generate_rd_installments(deposit_id: int, db: Session = Depends(get_db),
                             current: CurrentUser = Depends(require_admin)):
    """Generate monthly installment schedule for an RD deposit account."""
    deposit = db.query(DepositAccount).filter(DepositAccount.id == deposit_id).first()
    if not deposit:
        raise HTTPException(404, "Deposit not found")

    scheme = db.query(Scheme).filter(Scheme.id == deposit.scheme_id).first()
    scheme_type = scheme.scheme_type.value if hasattr(scheme.scheme_type, "value") else str(scheme.scheme_type)
    if scheme_type != "rd":
        raise HTTPException(400, "This is not a Recurring Deposit account")

    existing = db.query(RDInstallment).filter(RDInstallment.deposit_account_id == deposit_id).count()
    if existing > 0:
        raise HTTPException(400, "Installments already generated")

    if not scheme.tenure_months:
        raise HTTPException(400, "RD scheme has no tenure defined")

    monthly_amount = deposit.principal_amount  # principal_amount = monthly installment for RD
    start = deposit.opened_date

    for i in range(1, scheme.tenure_months + 1):
        due = start + relativedelta(months=i)
        db.add(RDInstallment(
            deposit_account_id=deposit_id,
            installment_no=i,
            due_date=due,
            amount_due=monthly_amount,
        ))

    db.commit()
    return {"message": f"{scheme.tenure_months} installments generated",
            "monthly_amount": monthly_amount}


def pay_rd_installment(deposit_id: int, amount: Decimal = Query(gt=0),
                       db: Session = Depends(get_db),
                       current: CurrentUser = Depends(require_admin)):
    """Pay the next due RD installment."""
    deposit = db.query(DepositAccount).filter(DepositAccount.id == deposit_id).first()
    if not deposit or deposit.status != DepositStatusEnum.active:
        raise HTTPException(400, "Deposit not found or not active")

    scheme = db.query(Scheme).filter(Scheme.id == deposit.scheme_id).first()
    member = db.query(Member).filter(Member.id == deposit.member_id).first()

    inst = (db.query(RDInstallment)
            .filter(RDInstallment.deposit_account_id == deposit_id, RDInstallment.is_paid == False)
            .order_by(RDInstallment.installment_no).first())

    if not inst:
        raise HTTPException(400, "All installments are paid")

    # Late penalty
    penalty = Decimal("0")
    if inst.due_date < date.today() and scheme and scheme.premature_penalty_pct > 0:
        penalty = (inst.amount_due * scheme.premature_penalty_pct / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP)
        inst.is_overdue = True

    inst.amount_paid = amount
    inst.penalty = penalty
    inst.paid_date = date.today()
    inst.is_paid = True

    # Journal: Dr Cash, Cr Member Deposit Account
    cash = _get_or_create_account(db, CASH_CODE, "Cash / Bank", AccountTypeEnum.asset)
    entry = _post_journal(db, "rd_installment",
                          f"RD installment #{inst.installment_no} for {deposit.account_number}",
                          cash.id, deposit.ledger_account_id, amount, current.user_id)
    inst.journal_entry_id = entry.id

    deposit.current_balance += amount

    db.commit()
    return {
        "message": f"Installment #{inst.installment_no} paid",
        "penalty": penalty,
        "new_balance": deposit.current_balance,
    }


def get_rd_schedule(deposit_id: int, db: Session = Depends(get_db),
                    current: CurrentUser = Depends(get_current_account)):
    deposit = db.query(DepositAccount).filter(DepositAccount.id == deposit_id).first()
    if not deposit:
        raise HTTPException(404, "Deposit not found")
    if current.role == "member" and deposit.member_id != current.member_id:
        raise HTTPException(403, "You can only view your own RD schedule")

    rows = (db.query(RDInstallment)
            .filter(RDInstallment.deposit_account_id == deposit_id)
            .order_by(RDInstallment.installment_no).all())

    return {
        "deposit_id": deposit_id,
        "account_number": deposit.account_number,
        "installments": [
            {"installment_no": r.installment_no, "due_date": r.due_date,
             "amount_due": r.amount_due, "amount_paid": r.amount_paid,
             "penalty": r.penalty, "paid_date": r.paid_date,
             "is_paid": r.is_paid, "is_overdue": r.is_overdue}
            for r in rows
        ],
    }
