"""Phase 6 — Dashboard analytics KPIs and dividend calculation."""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import uuid

from fastapi import Depends, Query, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_admin
from app.models.members import Member
from app.models.deposit import DepositAccount, DepositStatusEnum
from app.models.loan import LoanAccount, LoanStatusEnum, LoanRepayment
from app.models.share import ShareHolding, ShareTransaction, SHARE_DIVIDEND
from app.models.ledger import (
    Account, JournalEntry, JournalLine,
    AccountTypeEnum, OwnerTypeEnum, EntryStatusEnum,
)
from app.models.scheme import Scheme


SHARE_CAPITAL_CODE = "SHARE-CAP-001"
CASH_CODE = "CASH-001"


def _get_or_create_account(db, code, name, acct_type):
    acct = db.query(Account).filter(Account.code == code).first()
    if not acct:
        acct = Account(code=code, name=name, type=acct_type,
                       owner_type=OwnerTypeEnum.society, is_active=True)
        db.add(acct)
        db.flush()
    return acct


def _post_journal(db, txn_type, desc, dr_id, cr_id, amount, created_by):
    txn_ref = f"TXN-{uuid.uuid4().hex[:12].upper()}"
    entry = JournalEntry(txn_ref=txn_ref, txn_type=txn_type, description=desc,
                         created_by=created_by, status=EntryStatusEnum.posted)
    db.add(entry)
    db.flush()
    db.add(JournalLine(journal_entry_id=entry.id, account_id=dr_id,
                        dr_amount=amount, cr_amount=Decimal("0")))
    db.add(JournalLine(journal_entry_id=entry.id, account_id=cr_id,
                        dr_amount=Decimal("0"), cr_amount=amount))
    return entry


def dashboard_kpis(
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    """Key performance indicators for admin dashboard."""
    total_members = db.query(func.count(Member.id)).filter(Member.is_active == True).scalar() or 0

    # Deposits
    active_deposits = db.query(func.count(DepositAccount.id)).filter(
        DepositAccount.status == DepositStatusEnum.active).scalar() or 0
    total_deposit_balance = db.query(
        func.coalesce(func.sum(DepositAccount.current_balance), 0)
    ).filter(DepositAccount.status == DepositStatusEnum.active).scalar()

    # Loans
    active_loans = db.query(func.count(LoanAccount.id)).filter(
        LoanAccount.status == LoanStatusEnum.active).scalar() or 0
    total_loan_outstanding = db.query(
        func.coalesce(func.sum(LoanAccount.outstanding_principal), 0)
    ).filter(LoanAccount.status == LoanStatusEnum.active).scalar()

    # Overdue EMIs
    overdue_emis = db.query(func.count(LoanRepayment.id)).filter(
        LoanRepayment.is_paid == False,
        LoanRepayment.due_date < date.today()
    ).scalar() or 0

    # Share capital
    total_share_capital = db.query(
        func.coalesce(func.sum(ShareHolding.balance), 0)
    ).scalar()

    # Schemes
    active_schemes = db.query(func.count(Scheme.id)).filter(Scheme.is_active == True).scalar() or 0

    # Recent transactions (last 30 days)
    from datetime import timedelta
    thirty_days_ago = date.today() - timedelta(days=30)
    recent_txn_count = db.query(func.count(JournalEntry.id)).filter(
        JournalEntry.created_at >= thirty_days_ago).scalar() or 0

    return {
        "total_members": total_members,
        "active_deposits": active_deposits,
        "total_deposit_balance": Decimal(str(total_deposit_balance)),
        "active_loans": active_loans,
        "total_loan_outstanding": Decimal(str(total_loan_outstanding)),
        "overdue_emis": overdue_emis,
        "total_share_capital": Decimal(str(total_share_capital)),
        "active_schemes": active_schemes,
        "recent_transactions_30d": recent_txn_count,
        "deposit_to_loan_ratio": (
            round(float(total_deposit_balance) / float(total_loan_outstanding), 2)
            if float(total_loan_outstanding) > 0
            else None
        ),
    }


def dashboard_overview(
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    """Real time-series + recent activity for the dashboard charts/lists."""
    from sqlalchemy import text

    # Monthly share-money collections (last 12 months with data)
    coll = db.execute(text(
        "SELECT to_char(date_trunc('month', COALESCE(reference_month, txn_date)),'YYYY-MM') m, "
        "       round(SUM(amount),2) a "
        "FROM share_transactions WHERE txn_type = 'monthly_share_deposit' "
        "GROUP BY 1 ORDER BY 1"
    )).all()
    monthly_collections = [{"month": m, "amount": float(a)} for m, a in coll][-12:]

    # Member growth — cumulative members by joining month
    grow = db.execute(text(
        "SELECT to_char(date_trunc('month', date_of_joining),'YYYY-MM') m, COUNT(*) c "
        "FROM member_profiles WHERE date_of_joining IS NOT NULL GROUP BY 1 ORDER BY 1"
    )).all()
    member_growth, running = [], 0
    for m, c in grow:
        running += int(c)
        member_growth.append({"month": m, "total": running})
    member_growth = member_growth[-12:]

    # Recent transactions (share money)
    recent = db.execute(text(
        "SELECT m.name, st.amount, st.txn_type, st.txn_date, st.voucher_no "
        "FROM share_transactions st JOIN members m ON m.id = st.member_id "
        "ORDER BY st.id DESC LIMIT 8"
    )).all()
    recent_transactions = [
        {"name": n, "amount": float(a), "txn_type": t, "txn_date": str(d), "voucher_no": v}
        for n, a, t, d, v in recent
    ]

    # Recent members
    newm = db.execute(text(
        "SELECT name, membership_number FROM member_profiles ORDER BY id DESC LIMIT 6"
    )).all()
    recent_members = [{"name": n, "acno": a} for n, a in newm]

    return {
        "monthly_collections": monthly_collections,
        "member_growth": member_growth,
        "recent_transactions": recent_transactions,
        "recent_members": recent_members,
    }


def calculate_dividend(
    dividend_rate: Decimal = Query(gt=0, description="Dividend percentage on share value"),
    financial_year: str = Query(description="e.g. 2025-26"),
    post_entries: bool = Query(default=False, description="If true, post journal entries"),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    """Calculate (and optionally post) dividends for all shareholders."""
    holdings = (db.query(ShareHolding, Member.name)
                .join(Member, Member.id == ShareHolding.member_id)
                .filter(ShareHolding.balance > 0)
                .all())

    if not holdings:
        return {"message": "No shareholders found", "results": []}

    results = []
    total_dividend = Decimal("0")

    for holding, member_name in holdings:
        div_amount = (holding.balance * dividend_rate / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_dividend += div_amount

        entry_data = {
            "member_id": holding.member_id,
            "member_name": member_name,
            "share_balance": holding.balance,
            "dividend_rate": dividend_rate,
            "dividend_amount": div_amount,
        }

        if post_entries and div_amount > 0:
            # Journal: Dr Retained Earnings / P&L, Cr Cash (pay to member)
            # For simplicity: Dr Share Capital, Cr Cash
            cash = _get_or_create_account(db, CASH_CODE, "Cash / Bank", AccountTypeEnum.asset)
            div_exp = _get_or_create_account(db, "DIVIDEND-EXP-001", "Dividend Expense",
                                              AccountTypeEnum.expense)
            entry = _post_journal(db, "dividend",
                                  f"Dividend {financial_year} for {member_name} ({dividend_rate}%)",
                                  div_exp.id, cash.id, div_amount, current.user_id)

            db.add(ShareTransaction(
                member_id=holding.member_id,
                txn_type=SHARE_DIVIDEND,
                amount=div_amount, txn_date=date.today(),
                journal_entry_id=entry.id,
                remarks=f"Dividend {financial_year} @ {dividend_rate}%",
            ))
            entry_data["journal_entry_id"] = entry.id

        results.append(entry_data)

    if post_entries:
        db.commit()

    return {
        "financial_year": financial_year,
        "dividend_rate": dividend_rate,
        "total_dividend": total_dividend,
        "shareholders": len(results),
        "posted": post_entries,
        "results": results,
    }
