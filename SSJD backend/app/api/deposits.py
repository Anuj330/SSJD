from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
import uuid

from fastapi import Depends, HTTPException, Query
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_admin, get_current_account
from app.models.deposit import DepositAccount, DepositStatusEnum
from app.models.scheme import Scheme, SchemeTypeEnum
from app.models.ledger import (
    Account,
    JournalEntry,
    JournalLine,
    AccountTypeEnum,
    OwnerTypeEnum,
    EntryStatusEnum,
)
from app.models.members import Member
from app.schemas.deposit import DepositOpenRequest, DepositTransactionRequest
from app.services.ledger_service import (
    get_or_create_account as _get_or_create_system_account,
    post_journal as _post_journal,
)


# ── Well-known ledger account codes (created on first use) ──

CASH_ACCOUNT_CODE = "CASH-001"
INTEREST_EXPENSE_CODE = "INT-EXP-001"


def _generate_account_number(scheme_type: str) -> str:
    prefix = {"fd": "FD", "rd": "RD", "mis": "MIS", "savings": "SAV"}.get(scheme_type, "DEP")
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


# ─────────────────────────────────────────────
#  Open Deposit Account
# ─────────────────────────────────────────────

def open_deposit(
    payload: DepositOpenRequest,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    """Open a new deposit account for a member with an initial deposit."""
    # Validate member
    member = db.query(Member).filter(Member.id == payload.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Validate scheme
    scheme = db.query(Scheme).filter(Scheme.id == payload.scheme_id, Scheme.is_active == True).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found or inactive")

    # Validate amount against scheme limits
    if payload.amount < scheme.min_amount:
        raise HTTPException(status_code=400, detail=f"Minimum deposit is {scheme.min_amount}")
    if scheme.max_amount and payload.amount > scheme.max_amount:
        raise HTTPException(status_code=400, detail=f"Maximum deposit is {scheme.max_amount}")

    scheme_type_val = scheme.scheme_type.value if hasattr(scheme.scheme_type, "value") else str(scheme.scheme_type)
    acct_number = _generate_account_number(scheme_type_val)
    opened = payload.opened_date or date.today()

    # Calculate maturity date for term deposits
    maturity = None
    if scheme.tenure_months:
        from dateutil.relativedelta import relativedelta
        maturity = opened + relativedelta(months=scheme.tenure_months)

    # Create a member-owned liability ledger account
    ledger_acct = Account(
        code=f"DEP-{acct_number}",
        name=f"{scheme.name} – {member.name}",
        type=AccountTypeEnum.liability,
        owner_type=OwnerTypeEnum.member,
        owner_id=member.id,
        is_active=True,
    )
    db.add(ledger_acct)
    db.flush()

    # Create deposit account
    deposit = DepositAccount(
        account_number=acct_number,
        member_id=member.id,
        scheme_id=scheme.id,
        ledger_account_id=ledger_acct.id,
        principal_amount=payload.amount,
        current_balance=payload.amount,
        interest_earned=Decimal("0"),
        opened_date=opened,
        maturity_date=maturity,
        last_interest_date=opened,
        status=DepositStatusEnum.active,
    )
    db.add(deposit)
    db.flush()

    # Journal: Dr Cash/Bank (asset ↑), Cr Member Deposit (liability ↑)
    cash = _get_or_create_system_account(db, CASH_ACCOUNT_CODE, "Cash / Bank", AccountTypeEnum.asset)
    _post_journal(
        db,
        txn_type="deposit_open",
        description=f"Opening deposit {acct_number} for {member.name}",
        dr_account_id=cash.id,
        cr_account_id=ledger_acct.id,
        amount=payload.amount,
        created_by=current.user_id,
    )

    db.commit()
    db.refresh(deposit)
    return _deposit_dict(deposit, member.name, scheme.name)


# ─────────────────────────────────────────────
#  List / Get Deposits
# ─────────────────────────────────────────────

def list_deposits(
    member_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(get_current_account),
):
    query = (
        db.query(DepositAccount, Member.name.label("member_name"), Scheme.name.label("scheme_name"))
        .join(Member, Member.id == DepositAccount.member_id)
        .join(Scheme, Scheme.id == DepositAccount.scheme_id)
    )

    # Members can only see their own deposits
    if current.role == "member":
        query = query.filter(DepositAccount.member_id == current.member_id)
    elif member_id:
        query = query.filter(DepositAccount.member_id == member_id)

    if status:
        query = query.filter(DepositAccount.status == status)

    rows = query.order_by(DepositAccount.id.desc()).all()

    return [_deposit_dict(dep, m_name, s_name) for dep, m_name, s_name in rows]


def get_deposit(
    deposit_id: int,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(get_current_account),
):
    row = (
        db.query(DepositAccount, Member.name.label("member_name"), Scheme.name.label("scheme_name"))
        .join(Member, Member.id == DepositAccount.member_id)
        .join(Scheme, Scheme.id == DepositAccount.scheme_id)
        .filter(DepositAccount.id == deposit_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Deposit account not found")

    dep, m_name, s_name = row
    if current.role == "member" and dep.member_id != current.member_id:
        raise HTTPException(status_code=403, detail="You can only view your own deposits")

    return _deposit_dict(dep, m_name, s_name)


# ─────────────────────────────────────────────
#  Deposit Money (add funds to existing account)
# ─────────────────────────────────────────────

def deposit_money(
    deposit_id: int,
    payload: DepositTransactionRequest,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    deposit = db.query(DepositAccount).filter(DepositAccount.id == deposit_id).first()
    if not deposit:
        raise HTTPException(status_code=404, detail="Deposit account not found")
    if deposit.status != DepositStatusEnum.active:
        raise HTTPException(status_code=400, detail="Deposit account is not active")

    # Journal: Dr Cash (asset ↑), Cr Member Deposit (liability ↑)
    cash = _get_or_create_system_account(db, CASH_ACCOUNT_CODE, "Cash / Bank", AccountTypeEnum.asset)
    entry = _post_journal(
        db,
        txn_type="deposit",
        description=payload.description or f"Deposit to {deposit.account_number}",
        dr_account_id=cash.id,
        cr_account_id=deposit.ledger_account_id,
        amount=payload.amount,
        created_by=current.user_id,
    )

    deposit.principal_amount += payload.amount
    deposit.current_balance += payload.amount

    db.commit()
    db.refresh(deposit)
    return {
        "message": "Deposit successful",
        "journal_entry_id": entry.id,
        "new_balance": deposit.current_balance,
    }


# ─────────────────────────────────────────────
#  Withdraw Money
# ─────────────────────────────────────────────

def withdraw_money(
    deposit_id: int,
    payload: DepositTransactionRequest,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    deposit = db.query(DepositAccount).filter(DepositAccount.id == deposit_id).first()
    if not deposit:
        raise HTTPException(status_code=404, detail="Deposit account not found")
    if deposit.status != DepositStatusEnum.active:
        raise HTTPException(status_code=400, detail="Deposit account is not active")
    if payload.amount > deposit.current_balance:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    # Journal: Dr Member Deposit (liability ↓), Cr Cash (asset ↓)
    cash = _get_or_create_system_account(db, CASH_ACCOUNT_CODE, "Cash / Bank", AccountTypeEnum.asset)
    entry = _post_journal(
        db,
        txn_type="withdrawal",
        description=payload.description or f"Withdrawal from {deposit.account_number}",
        dr_account_id=deposit.ledger_account_id,
        cr_account_id=cash.id,
        amount=payload.amount,
        created_by=current.user_id,
    )

    deposit.current_balance -= payload.amount

    db.commit()
    db.refresh(deposit)
    return {
        "message": "Withdrawal successful",
        "journal_entry_id": entry.id,
        "new_balance": deposit.current_balance,
    }


# ─────────────────────────────────────────────
#  Close Deposit Account
# ─────────────────────────────────────────────

def close_deposit(
    deposit_id: int,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    deposit = db.query(DepositAccount).filter(DepositAccount.id == deposit_id).first()
    if not deposit:
        raise HTTPException(status_code=404, detail="Deposit account not found")
    if deposit.status not in (DepositStatusEnum.active, DepositStatusEnum.matured):
        raise HTTPException(status_code=400, detail="Deposit cannot be closed in current status")

    scheme = db.query(Scheme).filter(Scheme.id == deposit.scheme_id).first()
    is_premature = (
        deposit.maturity_date
        and date.today() < deposit.maturity_date
        and deposit.status == DepositStatusEnum.active
    )

    payout = deposit.current_balance

    # Apply premature penalty if applicable
    penalty = Decimal("0")
    if is_premature and scheme and scheme.premature_penalty_pct > 0:
        penalty = (deposit.interest_earned * scheme.premature_penalty_pct / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        payout -= penalty

    if payout > 0:
        # Journal: Dr Member Deposit (liability ↓), Cr Cash (asset ↓)
        cash = _get_or_create_system_account(db, CASH_ACCOUNT_CODE, "Cash / Bank", AccountTypeEnum.asset)
        _post_journal(
            db,
            txn_type="deposit_close",
            description=f"Closing deposit {deposit.account_number}" + (f" (penalty: {penalty})" if penalty else ""),
            dr_account_id=deposit.ledger_account_id,
            cr_account_id=cash.id,
            amount=payout,
            created_by=current.user_id,
        )

    deposit.status = DepositStatusEnum.premature_closed if is_premature else DepositStatusEnum.closed
    deposit.current_balance = Decimal("0")
    deposit.closed_at = func.now()

    db.commit()
    db.refresh(deposit)
    return {
        "message": "Deposit account closed",
        "payout": payout,
        "penalty": penalty,
        "status": deposit.status.value,
    }


# ─────────────────────────────────────────────
#  Calculate & Post Interest
# ─────────────────────────────────────────────

def calculate_interest(
    deposit_id: int,
    as_of: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    """Calculate and post accrued interest for a single deposit account."""
    deposit = db.query(DepositAccount).filter(DepositAccount.id == deposit_id).first()
    if not deposit:
        raise HTTPException(status_code=404, detail="Deposit account not found")
    if deposit.status != DepositStatusEnum.active:
        raise HTTPException(status_code=400, detail="Interest can only be calculated on active deposits")

    scheme = db.query(Scheme).filter(Scheme.id == deposit.scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=500, detail="Scheme not found for deposit")

    calc_date = as_of or date.today()
    from_date = deposit.last_interest_date or deposit.opened_date

    if calc_date <= from_date:
        raise HTTPException(status_code=400, detail="No new interest period to calculate")

    days = (calc_date - from_date).days
    rate = Decimal(str(scheme.interest_rate))
    principal = deposit.current_balance

    # Simple interest: P × R × T / (365 × 100)
    interest = (principal * rate * days / (Decimal("365") * Decimal("100"))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    if interest <= 0:
        raise HTTPException(status_code=400, detail="Calculated interest is zero")

    # Journal: Dr Interest Expense, Cr Member Deposit (liability ↑)
    int_exp = _get_or_create_system_account(db, INTEREST_EXPENSE_CODE, "Interest Expense", AccountTypeEnum.expense)
    entry = _post_journal(
        db,
        txn_type="interest_credit",
        description=f"Interest on {deposit.account_number} for {days} days @ {rate}%",
        dr_account_id=int_exp.id,
        cr_account_id=deposit.ledger_account_id,
        amount=interest,
        created_by=current.user_id,
    )

    deposit.interest_earned += interest
    deposit.current_balance += interest
    deposit.last_interest_date = calc_date

    db.commit()
    return {
        "deposit_id": deposit.id,
        "account_number": deposit.account_number,
        "days": days,
        "rate": rate,
        "interest_amount": interest,
        "journal_entry_id": entry.id,
    }


# ─────────────────────────────────────────────
#  Deposit Statement (ledger entries)
# ─────────────────────────────────────────────

def deposit_statement(
    deposit_id: int,
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(get_current_account),
):
    deposit = db.query(DepositAccount).filter(DepositAccount.id == deposit_id).first()
    if not deposit:
        raise HTTPException(status_code=404, detail="Deposit account not found")

    if current.role == "member" and deposit.member_id != current.member_id:
        raise HTTPException(status_code=403, detail="You can only view your own deposit statement")

    query = (
        db.query(JournalLine, JournalEntry)
        .join(JournalEntry, JournalEntry.id == JournalLine.journal_entry_id)
        .filter(JournalLine.account_id == deposit.ledger_account_id)
    )

    if from_date:
        query = query.filter(JournalEntry.created_at >= from_date)
    if to_date:
        query = query.filter(JournalEntry.created_at <= to_date)

    rows = query.order_by(JournalEntry.created_at.asc()).all()

    total_debit = Decimal("0")
    total_credit = Decimal("0")
    result = []
    for line, entry in rows:
        total_debit += Decimal(line.dr_amount)
        total_credit += Decimal(line.cr_amount)
        result.append({
            "entry_id": entry.id,
            "txn_ref": entry.txn_ref,
            "txn_type": entry.txn_type,
            "created_at": entry.created_at,
            "dr_amount": line.dr_amount,
            "cr_amount": line.cr_amount,
            "description": entry.description,
        })

    return {
        "deposit_id": deposit.id,
        "account_number": deposit.account_number,
        "current_balance": deposit.current_balance,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "rows": result,
    }


# ── Helper ──

def _deposit_dict(dep: DepositAccount, member_name: str = None, scheme_name: str = None) -> dict:
    return {
        "id": dep.id,
        "account_number": dep.account_number,
        "member_id": dep.member_id,
        "scheme_id": dep.scheme_id,
        "ledger_account_id": dep.ledger_account_id,
        "principal_amount": dep.principal_amount,
        "current_balance": dep.current_balance,
        "interest_earned": dep.interest_earned,
        "opened_date": dep.opened_date,
        "maturity_date": dep.maturity_date,
        "last_interest_date": dep.last_interest_date,
        "status": dep.status.value if hasattr(dep.status, "value") else str(dep.status),
        "created_at": dep.created_at,
        "member_name": member_name,
        "scheme_name": scheme_name,
    }
