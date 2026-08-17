"""PDF download endpoints for receipts, passbook, loan schedule, reports."""

import io
from datetime import date, datetime
from decimal import Decimal

from fastapi import Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_account, require_admin
from app.services.pdf_service import (
    generate_receipt_pdf, generate_passbook_pdf,
    generate_loan_schedule_pdf, generate_pnl_pdf, generate_balance_sheet_pdf,
)


def _pdf_response(pdf_bytes: bytes, filename: str):
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Receipt PDF ──

def receipt_pdf(
    entry_id: int,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(get_current_account),
):
    from app.models.ledger import JournalEntry, JournalLine, Account

    entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(404, "Journal entry not found")

    lines = (
        db.query(JournalLine, Account.name, Account.code)
        .join(Account, Account.id == JournalLine.account_id)
        .filter(JournalLine.journal_entry_id == entry_id)
        .all()
    )

    # RBAC: members can only see receipts for their own accounts
    if current.role == "member":
        from app.models.ledger import OwnerTypeEnum
        member_accts = {l.account_id for l, _, _ in lines}
        own_accts = {a.id for a in db.query(Account).filter(
            Account.owner_type == OwnerTypeEnum.member,
            Account.owner_id == current.member_id
        ).all()}
        if not member_accts & own_accts:
            raise HTTPException(403, "You can only view your own receipts")

    entry_data = {
        "txn_ref": entry.txn_ref,
        "txn_type": entry.txn_type,
        "description": entry.description,
        "status": entry.status.value if hasattr(entry.status, "value") else str(entry.status),
        "created_at": entry.created_at.strftime("%Y-%m-%d %H:%M") if entry.created_at else "",
    }
    lines_data = [
        {"account_name": name, "account_code": code,
         "dr_amount": line.dr_amount, "cr_amount": line.cr_amount}
        for line, name, code in lines
    ]

    pdf = generate_receipt_pdf(entry_data, lines_data)
    return _pdf_response(pdf, f"receipt_{entry.txn_ref}.pdf")


# ── Passbook PDF ──

def passbook_pdf(
    member_id: int,
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(get_current_account),
):
    if current.role == "member" and current.member_id != member_id:
        raise HTTPException(403, "You can only download your own passbook")

    from app.models.members import Member
    from app.models.ledger import Account, JournalEntry, JournalLine, OwnerTypeEnum

    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(404, "Member not found")

    member_accounts = db.query(Account).filter(
        Account.owner_type == OwnerTypeEnum.member,
        Account.owner_id == member_id,
    ).all()

    if not member_accounts:
        raise HTTPException(404, "No accounts found for member")

    acct_ids = [a.id for a in member_accounts]

    q = (
        db.query(JournalLine, JournalEntry)
        .join(JournalEntry, JournalEntry.id == JournalLine.journal_entry_id)
        .filter(JournalLine.account_id.in_(acct_ids))
    )
    if from_date:
        q = q.filter(JournalEntry.created_at >= from_date)
    if to_date:
        q = q.filter(JournalEntry.created_at <= to_date)

    results = q.order_by(JournalEntry.created_at.asc()).all()

    running = Decimal("0")
    rows = []
    total_cr = Decimal("0")
    total_dr = Decimal("0")

    for line, entry in results:
        cr = Decimal(str(line.cr_amount))
        dr = Decimal(str(line.dr_amount))
        running += cr - dr
        total_cr += cr
        total_dr += dr
        rows.append({
            "date": entry.created_at.strftime("%Y-%m-%d") if entry.created_at else "",
            "txn_type": entry.txn_type or "",
            "description": entry.description or "",
            "credit": float(cr),
            "debit": float(dr),
            "running_balance": float(running),
        })

    summary = {
        "current_balance": float(running),
        "total_credited": float(total_cr),
        "total_debited": float(total_dr),
    }

    pdf = generate_passbook_pdf(member.name, member_id, rows, summary, from_date, to_date)
    return _pdf_response(pdf, f"passbook_{member.name}_{date.today()}.pdf")


# ── Loan Schedule PDF ──

def loan_schedule_pdf(
    loan_id: int,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(get_current_account),
):
    from app.models.loan import LoanAccount, LoanRepayment, LoanProduct
    from app.models.members import Member

    loan = db.query(LoanAccount).filter(LoanAccount.id == loan_id).first()
    if not loan:
        raise HTTPException(404, "Loan not found")
    if current.role == "member" and loan.member_id != current.member_id:
        raise HTTPException(403, "You can only view your own loans")

    member = db.query(Member).filter(Member.id == loan.member_id).first()
    repayments = (
        db.query(LoanRepayment)
        .filter(LoanRepayment.loan_id == loan_id)
        .order_by(LoanRepayment.installment_no).all()
    )

    loan_data = {
        "loan_number": loan.loan_number,
        "member_name": member.name if member else "",
        "disbursed_amount": loan.disbursed_amount,
        "interest_rate": loan.interest_rate,
        "tenure_months": loan.tenure_months,
    }
    schedule = [
        {
            "installment_no": r.installment_no,
            "due_date": str(r.due_date),
            "principal_due": r.principal_due,
            "interest_due": r.interest_due,
            "total_due": r.total_due,
            "total_paid": r.total_paid,
            "is_paid": r.is_paid,
            "is_overdue": r.is_overdue,
        }
        for r in repayments
    ]

    pdf = generate_loan_schedule_pdf(loan_data, schedule)
    return _pdf_response(pdf, f"emi_schedule_{loan.loan_number}.pdf")


# ── P&L PDF ──

def pnl_pdf(
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    from app.api.reports import profit_and_loss as _pnl_logic
    # Call the existing report logic directly
    from app.models.ledger import Account, JournalEntry, JournalLine, AccountTypeEnum
    from sqlalchemy import func

    q = (
        db.query(Account.type, Account.code, Account.name,
                 func.coalesce(func.sum(JournalLine.dr_amount), 0),
                 func.coalesce(func.sum(JournalLine.cr_amount), 0))
        .join(JournalLine, JournalLine.account_id == Account.id)
        .join(JournalEntry, JournalEntry.id == JournalLine.journal_entry_id)
        .filter(Account.type.in_([AccountTypeEnum.income, AccountTypeEnum.expense]))
    )
    if from_date:
        q = q.filter(JournalEntry.created_at >= from_date)
    if to_date:
        q = q.filter(JournalEntry.created_at <= to_date)

    rows = q.group_by(Account.type, Account.code, Account.name).all()

    income, expenses = [], []
    ti, te = Decimal("0"), Decimal("0")
    for at, code, name, dr, cr in rows:
        t = at.value if hasattr(at, "value") else str(at)
        amt = Decimal(str(cr)) - Decimal(str(dr)) if t == "income" else Decimal(str(dr)) - Decimal(str(cr))
        entry = {"code": code, "name": name, "amount": float(amt)}
        if t == "income":
            income.append(entry)
            ti += amt
        else:
            expenses.append(entry)
            te += amt

    data = {"income": income, "total_income": float(ti), "expenses": expenses,
            "total_expenses": float(te), "net_profit": float(ti - te),
            "from_date": str(from_date) if from_date else None,
            "to_date": str(to_date) if to_date else None}

    pdf = generate_pnl_pdf(data)
    return _pdf_response(pdf, f"pnl_{date.today()}.pdf")


# ── Balance Sheet PDF ──

def balance_sheet_pdf(
    as_of: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    from app.models.ledger import Account, JournalEntry, JournalLine, AccountTypeEnum
    from sqlalchemy import func

    q = (
        db.query(Account.type, Account.code, Account.name,
                 func.coalesce(func.sum(JournalLine.dr_amount), 0),
                 func.coalesce(func.sum(JournalLine.cr_amount), 0))
        .join(JournalLine, JournalLine.account_id == Account.id)
        .join(JournalEntry, JournalEntry.id == JournalLine.journal_entry_id)
        .filter(Account.type.in_([AccountTypeEnum.asset, AccountTypeEnum.liability, AccountTypeEnum.equity]))
    )
    if as_of:
        q = q.filter(JournalEntry.created_at <= as_of)

    rows = q.group_by(Account.type, Account.code, Account.name).all()

    assets, liabilities, equity = [], [], []
    ta, tl, te = Decimal("0"), Decimal("0"), Decimal("0")
    for at, code, name, dr, cr in rows:
        t = at.value if hasattr(at, "value") else str(at)
        if t == "asset":
            b = Decimal(str(dr)) - Decimal(str(cr))
            assets.append({"code": code, "name": name, "balance": float(b)})
            ta += b
        elif t == "liability":
            b = Decimal(str(cr)) - Decimal(str(dr))
            liabilities.append({"code": code, "name": name, "balance": float(b)})
            tl += b
        else:
            b = Decimal(str(cr)) - Decimal(str(dr))
            equity.append({"code": code, "name": name, "balance": float(b)})
            te += b

    data = {"assets": assets, "total_assets": float(ta), "liabilities": liabilities,
            "total_liabilities": float(tl), "equity": equity, "total_equity": float(te),
            "is_balanced": ta == (tl + te), "as_of": str(as_of) if as_of else str(date.today())}

    pdf = generate_balance_sheet_pdf(data)
    return _pdf_response(pdf, f"balance_sheet_{date.today()}.pdf")
