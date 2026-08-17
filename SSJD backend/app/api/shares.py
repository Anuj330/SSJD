from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
import uuid

from dateutil.relativedelta import relativedelta
from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_admin, get_current_account
from app.models.share import (
    ShareHolding, ShareTransaction, RDInstallment,
    SHARE_DEPOSIT, SHARE_WITHDRAWAL, gen_share_txn_id,
)
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

def purchase_shares(member_id: int, amount: Decimal | None = Query(default=None, gt=0),
                    cd_amount: Decimal | None = Query(default=None, ge=0, description="Compulsory Deposit portion"),
                    od_amount: Decimal | None = Query(default=None, ge=0, description="Optional Deposit portion"),
                    remarks: str | None = Query(default=None),
                    txn_date: str | None = Query(default=None, description="Deposit date YYYY-MM-DD (default today)"),
                    db: Session = Depends(get_db),
                    current: CurrentUser = Depends(require_admin)):
    """Record a member's share-money deposit. Share money (SM) = CD + OD."""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(404, "Member not found")

    d = date.today()
    if txn_date:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                d = datetime.strptime(txn_date.strip(), fmt).date()
                break
            except ValueError:
                continue
    ref_month = date(d.year, d.month, 1)

    txn_id, holding, amt = deposit_share(db, member, amount, d, ref_month, remarks,
                                         current.user_id, cd_amount=cd_amount, od_amount=od_amount)

    db.commit()
    _notify_share_deposit(db, member, amt)
    return {"message": "Share money deposited", "transaction_id": txn_id,
            "balance": holding.balance, "cd_balance": holding.cd_balance, "od_balance": holding.od_balance}


def _resolve_cd_od(amount, cd_amount, od_amount):
    """Reconcile the CD/OD split with the SM total. Rules:
    - if only cd/od given → amount = cd + od
    - if only amount given → default the whole amount to CD (compulsory)
    - if all given → cd + od must equal amount
    Returns (amount, cd, od) as Decimals.
    """
    cd = Decimal(str(cd_amount)) if cd_amount is not None else None
    od = Decimal(str(od_amount)) if od_amount is not None else None
    amt = Decimal(str(amount)) if amount is not None else None

    if cd is None and od is None:
        if amt is None or amt <= 0:
            raise HTTPException(400, "Provide an amount, or a CD/OD split")
        return amt, amt, Decimal("0")

    cd = cd or Decimal("0")
    od = od or Decimal("0")
    split_total = cd + od
    if amt is None:
        amt = split_total
    if amt <= 0:
        raise HTTPException(400, "Amount must be greater than 0")
    if split_total != amt:
        raise HTTPException(400, f"CD ({cd}) + OD ({od}) must equal the share amount ({amt})")
    return amt, cd, od


def deposit_share(db, member, amount, d, ref_month, remarks, created_by,
                  cd_amount=None, od_amount=None):
    """Post a share-money deposit (no commit). SM = CD + OD; both accumulate in
    their own running balances. Returns (transaction_id, holding)."""
    amount, cd, od = _resolve_cd_od(amount, cd_amount, od_amount)

    holding = db.query(ShareHolding).filter(ShareHolding.member_id == member.id).first()
    if not holding:
        holding = ShareHolding(member_id=member.id, balance=Decimal("0"),
                               cd_balance=Decimal("0"), od_balance=Decimal("0"))
        db.add(holding)
        db.flush()

    # Journal: Dr Cash, Cr Share Capital (money received and held for the member)
    cash = _get_or_create_account(db, CASH_CODE, "Cash / Bank", AccountTypeEnum.asset)
    share_cap = _get_or_create_account(db, SHARE_CAPITAL_CODE, "Share Capital", AccountTypeEnum.equity)
    entry = _post_journal(db, SHARE_DEPOSIT,
                          f"Share money deposit by {member.name} (CD {cd} / OD {od})",
                          cash.id, share_cap.id, amount, created_by)

    holding.balance += amount
    holding.cd_balance = (holding.cd_balance or Decimal("0")) + cd
    holding.od_balance = (holding.od_balance or Decimal("0")) + od

    txn_id = gen_share_txn_id()
    db.add(ShareTransaction(
        transaction_id=txn_id, member_id=member.id, txn_type=SHARE_DEPOSIT,
        amount=amount, cd_amount=cd, od_amount=od, txn_date=d, reference_month=ref_month,
        journal_entry_id=entry.id, remarks=(remarks or None),
    ))
    return txn_id, holding, amount


def _notify_share_deposit(db, member, amount):
    """Best-effort WhatsApp confirmation for a share-money deposit (never blocks)."""
    try:
        from app.services.notify_service import send_whatsapp
        from app.models.member_profile import MemberProfile
        prof = db.query(MemberProfile).filter(MemberProfile.member_id == member.id).first()
        phone = (member.phone if member else None) or (prof.phone_number if prof else None)
        if not (member and phone):
            return
        msg = (f"Hi {member.name}, SSJD Cooperative received your share money "
               f"deposit of Rs {amount}. Thank you.")
        send_whatsapp(phone, msg)
    except Exception:
        pass


def refund_shares(member_id: int, amount: Decimal = Query(gt=0),
                  remarks: str | None = Query(default=None),
                  db: Session = Depends(get_db),
                  current: CurrentUser = Depends(require_admin)):
    """Withdraw money from a member's share-money account."""
    holding = db.query(ShareHolding).filter(ShareHolding.member_id == member_id).first()
    if not holding or holding.balance < amount:
        raise HTTPException(400, "Insufficient balance")

    member = db.query(Member).filter(Member.id == member_id).first()

    cash = _get_or_create_account(db, CASH_CODE, "Cash / Bank", AccountTypeEnum.asset)
    share_cap = _get_or_create_account(db, SHARE_CAPITAL_CODE, "Share Capital", AccountTypeEnum.equity)
    entry = _post_journal(db, SHARE_WITHDRAWAL,
                          f"Share money withdrawal for {member.name}",
                          share_cap.id, cash.id, amount, current.user_id)

    holding.balance -= amount

    txn_id = gen_share_txn_id()
    db.add(ShareTransaction(
        transaction_id=txn_id, member_id=member_id, txn_type=SHARE_WITHDRAWAL,
        amount=amount, txn_date=date.today(),
        journal_entry_id=entry.id, remarks=(remarks or None),
    ))

    db.commit()
    return {"message": "Share money withdrawn", "transaction_id": txn_id, "balance": holding.balance}


def get_member_shares(member_id: int, db: Session = Depends(get_db),
                      current: CurrentUser = Depends(get_current_account)):
    if current.role == "member" and current.member_id != member_id:
        raise HTTPException(403, "You can only view your own share money")

    holding = db.query(ShareHolding).filter(ShareHolding.member_id == member_id).first()
    txns = (db.query(ShareTransaction)
            .filter(ShareTransaction.member_id == member_id)
            .order_by(ShareTransaction.txn_date.desc(), ShareTransaction.id.desc()).all())

    return {
        "member_id": member_id,
        "balance": holding.balance if holding else 0,
        "cd_balance": holding.cd_balance if holding else 0,
        "od_balance": holding.od_balance if holding else 0,
        "transactions": [
            {"id": t.id, "transaction_id": t.transaction_id, "txn_type": t.txn_type,
             "amount": t.amount, "cd_amount": t.cd_amount, "od_amount": t.od_amount,
             "txn_date": t.txn_date, "created_at": t.created_at, "remarks": t.remarks}
            for t in txns
        ],
    }


SHARE_INTEREST_RATE = Decimal("6")  # % per annum, society policy


def share_interest(member_id: int, rate: Decimal = Query(default=SHARE_INTEREST_RATE),
                   as_of: str = Query(default=None),
                   db: Session = Depends(get_db),
                   current: CurrentUser = Depends(get_current_account)):
    """RD-style interest on share money: each deposit earns simple interest for the
    number of completed months it has been held, at `rate`% per annum."""
    if current.role == "member" and current.member_id != member_id:
        raise HTTPException(403, "You can only view your own interest")

    asof = date.today()
    if as_of:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                asof = datetime.strptime(as_of, fmt).date()
                break
            except ValueError:
                continue

    monthly_rate = Decimal(str(rate)) / Decimal("12") / Decimal("100")
    txns = (db.query(ShareTransaction)
            .filter(ShareTransaction.member_id == member_id)
            .order_by(ShareTransaction.txn_date).all())

    principal = Decimal("0")
    total_interest = Decimal("0")
    breakdown = []
    for t in txns:
        d = t.txn_date or t.reference_month
        signed = -Decimal(t.amount) if str(t.txn_type).lower() == "withdrawal" else Decimal(t.amount)
        months_active = (asof.year - d.year) * 12 + (asof.month - d.month)
        # Deposits made after the 15th earn no interest for that month.
        if d.day > 15:
            months_active -= 1
        if months_active < 0:
            months_active = 0
        interest = (signed * monthly_rate * months_active).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        principal += signed
        total_interest += interest
        breakdown.append({
            "date": str(d), "amount": signed, "months_active": months_active,
            "interest": interest,
        })

    return {
        "member_id": member_id,
        "rate": rate,
        "as_of": str(asof),
        "principal": principal,
        "total_interest": total_interest,
        "balance_with_interest": principal + total_interest,
        "breakdown": breakdown,
    }


def list_all_shares(db: Session = Depends(get_db),
                    current: CurrentUser = Depends(require_admin)):
    holdings = (db.query(ShareHolding, Member.name)
                .join(Member, Member.id == ShareHolding.member_id)
                .order_by(ShareHolding.member_id).all())
    return [
        {"member_id": h.member_id, "member_name": name, "balance": h.balance}
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
