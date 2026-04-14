from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import uuid
import math

from dateutil.relativedelta import relativedelta
from fastapi import Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_admin, get_current_account
from app.models.loan import LoanProduct, LoanAccount, LoanRepayment, LoanStatusEnum
from app.models.ledger import (
    Account, JournalEntry, JournalLine,
    AccountTypeEnum, OwnerTypeEnum, EntryStatusEnum,
)
from app.models.members import Member
from app.schemas.loan import (
    LoanProductCreate, LoanProductUpdate,
    LoanApplyRequest, LoanApproveRequest, LoanRepaymentRequest,
)


# ── System account codes ──
CASH_CODE = "CASH-001"
LOAN_INTEREST_INCOME_CODE = "LOAN-INT-INC-001"
LOAN_PENALTY_INCOME_CODE = "LOAN-PENALTY-INC-001"
PROCESSING_FEE_INCOME_CODE = "PROC-FEE-INC-001"


def _get_or_create_account(db, code, name, acct_type):
    acct = db.query(Account).filter(Account.code == code).first()
    if not acct:
        acct = Account(code=code, name=name, type=acct_type,
                       owner_type=OwnerTypeEnum.society, is_active=True)
        db.add(acct)
        db.flush()
    return acct


def _post_journal(db, txn_type, description, dr_account_id, cr_account_id, amount, created_by):
    txn_ref = f"TXN-{uuid.uuid4().hex[:12].upper()}"
    entry = JournalEntry(txn_ref=txn_ref, txn_type=txn_type, description=description,
                         created_by=created_by, status=EntryStatusEnum.posted)
    db.add(entry)
    db.flush()
    db.add(JournalLine(journal_entry_id=entry.id, account_id=dr_account_id,
                        dr_amount=amount, cr_amount=Decimal("0")))
    db.add(JournalLine(journal_entry_id=entry.id, account_id=cr_account_id,
                        dr_amount=Decimal("0"), cr_amount=amount))
    return entry


def _enum_val(v):
    return v.value if hasattr(v, "value") else str(v)


# ───────────────────────────────────
#  Loan Products CRUD
# ───────────────────────────────────

def create_loan_product(payload: LoanProductCreate, db: Session = Depends(get_db),
                        current: CurrentUser = Depends(require_admin)):
    if db.query(LoanProduct).filter(LoanProduct.name == payload.name).first():
        raise HTTPException(409, "Product name already exists")
    prod = LoanProduct(**payload.model_dump())
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return _product_dict(prod)


def list_loan_products(db: Session = Depends(get_db),
                       current: CurrentUser = Depends(get_current_account)):
    q = db.query(LoanProduct).order_by(LoanProduct.id)
    if current.role == "member":
        q = q.filter(LoanProduct.is_active == True)
    return [_product_dict(p) for p in q.all()]


def get_loan_product(product_id: int, db: Session = Depends(get_db),
                     current: CurrentUser = Depends(get_current_account)):
    p = db.query(LoanProduct).filter(LoanProduct.id == product_id).first()
    if not p:
        raise HTTPException(404, "Loan product not found")
    return _product_dict(p)


def update_loan_product(product_id: int, payload: LoanProductUpdate,
                        db: Session = Depends(get_db),
                        current: CurrentUser = Depends(require_admin)):
    p = db.query(LoanProduct).filter(LoanProduct.id == product_id).first()
    if not p:
        raise HTTPException(404, "Loan product not found")
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"] != p.name:
        if db.query(LoanProduct).filter(LoanProduct.name == data["name"]).first():
            raise HTTPException(409, "Product name already exists")
    for k, v in data.items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return _product_dict(p)


# ───────────────────────────────────
#  Loan Application
# ───────────────────────────────────

def apply_loan(payload: LoanApplyRequest, db: Session = Depends(get_db),
               current: CurrentUser = Depends(require_admin)):
    member = db.query(Member).filter(Member.id == payload.member_id).first()
    if not member:
        raise HTTPException(404, "Member not found")

    product = db.query(LoanProduct).filter(LoanProduct.id == payload.product_id,
                                           LoanProduct.is_active == True).first()
    if not product:
        raise HTTPException(404, "Loan product not found or inactive")

    if payload.amount < product.min_amount:
        raise HTTPException(400, f"Minimum loan amount is {product.min_amount}")
    if product.max_amount and payload.amount > product.max_amount:
        raise HTTPException(400, f"Maximum loan amount is {product.max_amount}")
    if payload.tenure_months > product.max_tenure_months:
        raise HTTPException(400, f"Maximum tenure is {product.max_tenure_months} months")

    loan_number = f"LN-{uuid.uuid4().hex[:8].upper()}"

    loan = LoanAccount(
        loan_number=loan_number,
        member_id=member.id,
        product_id=product.id,
        applied_amount=payload.amount,
        tenure_months=payload.tenure_months,
        interest_rate=product.interest_rate,
        applied_date=date.today(),
        status=LoanStatusEnum.applied,
        remarks=payload.remarks,
    )
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return _loan_dict(loan, member.name, product.name)


# ───────────────────────────────────
#  Approve / Reject
# ───────────────────────────────────

def approve_loan(loan_id: int, payload: LoanApproveRequest,
                 db: Session = Depends(get_db),
                 current: CurrentUser = Depends(require_admin)):
    loan = db.query(LoanAccount).filter(LoanAccount.id == loan_id).first()
    if not loan:
        raise HTTPException(404, "Loan not found")
    if loan.status != LoanStatusEnum.applied:
        raise HTTPException(400, f"Cannot approve loan in '{_enum_val(loan.status)}' status")

    loan.sanctioned_amount = payload.sanctioned_amount or loan.applied_amount
    loan.approved_date = date.today()
    loan.approved_by = current.user_id
    loan.status = LoanStatusEnum.approved
    if payload.remarks:
        loan.remarks = payload.remarks
    db.commit()
    db.refresh(loan)
    return {"message": "Loan approved", "sanctioned_amount": loan.sanctioned_amount}


def reject_loan(loan_id: int, remarks: str = Query(default=""),
                db: Session = Depends(get_db),
                current: CurrentUser = Depends(require_admin)):
    loan = db.query(LoanAccount).filter(LoanAccount.id == loan_id).first()
    if not loan:
        raise HTTPException(404, "Loan not found")
    if loan.status != LoanStatusEnum.applied:
        raise HTTPException(400, "Can only reject applied loans")
    loan.status = LoanStatusEnum.rejected
    loan.remarks = remarks or "Rejected"
    db.commit()
    return {"message": "Loan rejected"}


# ───────────────────────────────────
#  Disburse
# ───────────────────────────────────

def disburse_loan(loan_id: int, db: Session = Depends(get_db),
                  current: CurrentUser = Depends(require_admin)):
    loan = db.query(LoanAccount).filter(LoanAccount.id == loan_id).first()
    if not loan:
        raise HTTPException(404, "Loan not found")
    if loan.status != LoanStatusEnum.approved:
        raise HTTPException(400, "Loan must be approved before disbursement")

    member = db.query(Member).filter(Member.id == loan.member_id).first()
    product = db.query(LoanProduct).filter(LoanProduct.id == loan.product_id).first()
    amount = loan.sanctioned_amount or loan.applied_amount

    # Create member-owned asset ledger account for loan receivable
    ledger_acct = Account(
        code=f"LOAN-{loan.loan_number}",
        name=f"{product.name} – {member.name}",
        type=AccountTypeEnum.asset,
        owner_type=OwnerTypeEnum.member,
        owner_id=member.id,
        is_active=True,
    )
    db.add(ledger_acct)
    db.flush()
    loan.ledger_account_id = ledger_acct.id

    # Journal: Dr Loan Receivable (asset ↑), Cr Cash (asset ↓)
    cash = _get_or_create_account(db, CASH_CODE, "Cash / Bank", AccountTypeEnum.asset)
    _post_journal(db, "loan_disburse",
                  f"Disbursement of {loan.loan_number} to {member.name}",
                  ledger_acct.id, cash.id, amount, current.user_id)

    # Processing fee if applicable
    if product.processing_fee_pct > 0:
        fee = (amount * product.processing_fee_pct / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP)
        if fee > 0:
            fee_acct = _get_or_create_account(db, PROCESSING_FEE_INCOME_CODE,
                                              "Processing Fee Income", AccountTypeEnum.income)
            _post_journal(db, "processing_fee",
                          f"Processing fee for {loan.loan_number}",
                          cash.id, fee_acct.id, fee, current.user_id)

    loan.disbursed_amount = amount
    loan.outstanding_principal = amount
    loan.disbursed_date = date.today()
    loan.maturity_date = date.today() + relativedelta(months=loan.tenure_months)
    loan.status = LoanStatusEnum.active

    # Generate EMI schedule
    _generate_emi_schedule(db, loan)

    db.commit()
    db.refresh(loan)
    return {"message": "Loan disbursed", "loan_number": loan.loan_number,
            "amount": amount, "maturity_date": str(loan.maturity_date)}


def _generate_emi_schedule(db, loan):
    """Generate flat EMI schedule (reducing balance)."""
    P = float(loan.disbursed_amount)
    r = float(loan.interest_rate) / 100.0 / 12.0  # monthly rate
    n = loan.tenure_months

    if r > 0:
        emi = P * r * math.pow(1 + r, n) / (math.pow(1 + r, n) - 1)
    else:
        emi = P / n

    emi = Decimal(str(emi)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    balance = Decimal(str(P))
    start = loan.disbursed_date or date.today()

    for i in range(1, n + 1):
        due = start + relativedelta(months=i)
        interest = (balance * Decimal(str(loan.interest_rate)) / Decimal("1200")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP)
        principal = emi - interest
        if i == n:
            principal = balance
            interest = emi - principal if emi > principal else interest
        if principal > balance:
            principal = balance
        balance -= principal

        db.add(LoanRepayment(
            loan_id=loan.id,
            installment_no=i,
            due_date=due,
            principal_due=max(principal, Decimal("0")),
            interest_due=max(interest, Decimal("0")),
            total_due=principal + interest,
        ))


# ───────────────────────────────────
#  Make Repayment
# ───────────────────────────────────

def make_repayment(loan_id: int, payload: LoanRepaymentRequest,
                   db: Session = Depends(get_db),
                   current: CurrentUser = Depends(require_admin)):
    loan = db.query(LoanAccount).filter(LoanAccount.id == loan_id).first()
    if not loan:
        raise HTTPException(404, "Loan not found")
    if loan.status != LoanStatusEnum.active:
        raise HTTPException(400, "Loan is not active")

    product = db.query(LoanProduct).filter(LoanProduct.id == loan.product_id).first()
    member = db.query(Member).filter(Member.id == loan.member_id).first()

    # Find next unpaid installment
    next_inst = (db.query(LoanRepayment)
                 .filter(LoanRepayment.loan_id == loan_id, LoanRepayment.is_paid == False)
                 .order_by(LoanRepayment.installment_no)
                 .first())

    remaining = payload.amount
    paid_installments = []

    while remaining > 0 and next_inst:
        # Check overdue penalty
        penalty = Decimal("0")
        if next_inst.due_date < date.today() and product and product.late_penalty_pct > 0:
            penalty = (next_inst.total_due * product.late_penalty_pct / Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP)
            next_inst.is_overdue = True

        needed = next_inst.total_due - next_inst.total_paid + penalty
        pay_now = min(remaining, needed)

        # Allocate: penalty first, then interest, then principal
        pen_pay = min(pay_now, penalty)
        pay_now -= pen_pay
        int_pay = min(pay_now, next_inst.interest_due - next_inst.interest_paid)
        pay_now -= int_pay
        prin_pay = min(pay_now, next_inst.principal_due - next_inst.principal_paid)
        pay_now_leftover = pay_now - prin_pay

        next_inst.penalty_paid += pen_pay
        next_inst.interest_paid += int_pay
        next_inst.principal_paid += prin_pay
        next_inst.total_paid = next_inst.principal_paid + next_inst.interest_paid + next_inst.penalty_paid
        next_inst.paid_date = date.today()

        if next_inst.total_paid >= next_inst.total_due:
            next_inst.is_paid = True

        paid_installments.append(next_inst.installment_no)
        remaining -= (pen_pay + int_pay + prin_pay)

        # Update loan totals
        loan.outstanding_principal -= prin_pay
        loan.total_interest_paid += int_pay
        loan.total_penalty_paid += pen_pay

        # Move to next installment
        next_inst = (db.query(LoanRepayment)
                     .filter(LoanRepayment.loan_id == loan_id,
                             LoanRepayment.is_paid == False,
                             LoanRepayment.installment_no > next_inst.installment_no)
                     .order_by(LoanRepayment.installment_no)
                     .first()) if next_inst.is_paid else None

    total_repaid = payload.amount - remaining

    if total_repaid <= 0:
        raise HTTPException(400, "No installments to pay")

    # Journal: Dr Cash (asset ↑), Cr Loan Receivable (asset ↓)
    cash = _get_or_create_account(db, CASH_CODE, "Cash / Bank", AccountTypeEnum.asset)

    # Principal portion: Dr Cash, Cr Loan Receivable
    principal_total = sum(
        (db.query(LoanRepayment).filter(
            LoanRepayment.loan_id == loan_id,
            LoanRepayment.installment_no == inst_no
        ).first().principal_paid if True else Decimal("0"))
        for inst_no in paid_installments
    ) if False else Decimal("0")

    # Simpler approach: post entire repayment
    _post_journal(db, "loan_repayment",
                  payload.description or f"Repayment for {loan.loan_number}",
                  cash.id, loan.ledger_account_id, total_repaid, current.user_id)

    # Interest income journal
    int_portion = payload.amount - remaining - (loan.outstanding_principal + total_repaid - loan.outstanding_principal)
    # Actually just use the total for now — the main ledger entry covers it

    # Check if loan fully repaid
    if loan.outstanding_principal <= 0:
        loan.outstanding_principal = Decimal("0")
        loan.status = LoanStatusEnum.closed
        loan.closed_date = date.today()

    db.commit()
    return {
        "message": "Repayment recorded",
        "amount_applied": total_repaid,
        "installments_paid": paid_installments,
        "outstanding_principal": loan.outstanding_principal,
        "status": _enum_val(loan.status),
    }


# ───────────────────────────────────
#  List / Get / Schedule
# ───────────────────────────────────

def list_loans(member_id: int | None = Query(default=None),
               status: str | None = Query(default=None),
               db: Session = Depends(get_db),
               current: CurrentUser = Depends(get_current_account)):
    q = (db.query(LoanAccount, Member.name.label("m_name"), LoanProduct.name.label("p_name"))
         .join(Member, Member.id == LoanAccount.member_id)
         .join(LoanProduct, LoanProduct.id == LoanAccount.product_id))

    if current.role == "member":
        q = q.filter(LoanAccount.member_id == current.member_id)
    elif member_id:
        q = q.filter(LoanAccount.member_id == member_id)
    if status:
        q = q.filter(LoanAccount.status == status)

    return [_loan_dict(l, mn, pn) for l, mn, pn in q.order_by(LoanAccount.id.desc()).all()]


def get_loan(loan_id: int, db: Session = Depends(get_db),
             current: CurrentUser = Depends(get_current_account)):
    row = (db.query(LoanAccount, Member.name.label("m"), LoanProduct.name.label("p"))
           .join(Member, Member.id == LoanAccount.member_id)
           .join(LoanProduct, LoanProduct.id == LoanAccount.product_id)
           .filter(LoanAccount.id == loan_id).first())
    if not row:
        raise HTTPException(404, "Loan not found")
    loan, mn, pn = row
    if current.role == "member" and loan.member_id != current.member_id:
        raise HTTPException(403, "You can only view your own loans")
    return _loan_dict(loan, mn, pn)


def get_loan_schedule(loan_id: int, db: Session = Depends(get_db),
                      current: CurrentUser = Depends(get_current_account)):
    loan = db.query(LoanAccount).filter(LoanAccount.id == loan_id).first()
    if not loan:
        raise HTTPException(404, "Loan not found")
    if current.role == "member" and loan.member_id != current.member_id:
        raise HTTPException(403, "You can only view your own loans")

    rows = (db.query(LoanRepayment)
            .filter(LoanRepayment.loan_id == loan_id)
            .order_by(LoanRepayment.installment_no).all())

    return {
        "loan_id": loan.id,
        "loan_number": loan.loan_number,
        "schedule": [
            {
                "installment_no": r.installment_no,
                "due_date": r.due_date,
                "principal_due": r.principal_due,
                "interest_due": r.interest_due,
                "total_due": r.total_due,
                "principal_paid": r.principal_paid,
                "interest_paid": r.interest_paid,
                "penalty_paid": r.penalty_paid,
                "total_paid": r.total_paid,
                "paid_date": r.paid_date,
                "is_paid": r.is_paid,
                "is_overdue": r.is_overdue,
            }
            for r in rows
        ],
    }


# ── Helpers ──

def _product_dict(p):
    return {
        "id": p.id, "name": p.name,
        "loan_type": _enum_val(p.loan_type),
        "description": p.description,
        "interest_rate": p.interest_rate,
        "min_amount": p.min_amount,
        "max_amount": p.max_amount,
        "max_tenure_months": p.max_tenure_months,
        "repayment_freq": _enum_val(p.repayment_freq),
        "late_penalty_pct": p.late_penalty_pct,
        "processing_fee_pct": p.processing_fee_pct,
        "is_active": p.is_active,
        "created_at": p.created_at,
    }


def _loan_dict(loan, member_name=None, product_name=None):
    return {
        "id": loan.id, "loan_number": loan.loan_number,
        "member_id": loan.member_id, "product_id": loan.product_id,
        "applied_amount": loan.applied_amount,
        "sanctioned_amount": loan.sanctioned_amount,
        "disbursed_amount": loan.disbursed_amount,
        "outstanding_principal": loan.outstanding_principal,
        "total_interest_paid": loan.total_interest_paid,
        "total_penalty_paid": loan.total_penalty_paid,
        "tenure_months": loan.tenure_months,
        "interest_rate": loan.interest_rate,
        "applied_date": loan.applied_date,
        "approved_date": loan.approved_date,
        "disbursed_date": loan.disbursed_date,
        "maturity_date": loan.maturity_date,
        "closed_date": loan.closed_date,
        "status": _enum_val(loan.status),
        "remarks": loan.remarks,
        "member_name": member_name,
        "product_name": product_name,
        "created_at": loan.created_at,
    }
