"""Phase 4 — Financial reports: P&L, Balance Sheet, Member Outstanding, Batch Interest."""

from datetime import date, datetime
from decimal import Decimal

from fastapi import Depends, HTTPException, Query
from sqlalchemy import func, and_, case
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_admin
from app.models.ledger import Account, JournalEntry, JournalLine, AccountTypeEnum, EntryStatusEnum
from app.models.members import Member
from app.models.deposit import DepositAccount, DepositStatusEnum
from app.models.loan import LoanAccount, LoanStatusEnum, LoanRepayment
from app.models.share import ShareHolding


def profit_and_loss(
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    """Income vs Expense report."""
    q = (
        db.query(
            Account.type,
            Account.code,
            Account.name,
            func.coalesce(func.sum(JournalLine.dr_amount), 0).label("total_dr"),
            func.coalesce(func.sum(JournalLine.cr_amount), 0).label("total_cr"),
        )
        .join(JournalLine, JournalLine.account_id == Account.id)
        .join(JournalEntry, JournalEntry.id == JournalLine.journal_entry_id)
        .filter(Account.type.in_([AccountTypeEnum.income, AccountTypeEnum.expense]))
    )
    if from_date:
        q = q.filter(JournalEntry.created_at >= from_date)
    if to_date:
        q = q.filter(JournalEntry.created_at <= to_date)

    rows = q.group_by(Account.type, Account.code, Account.name).order_by(Account.type, Account.code).all()

    income_rows = []
    expense_rows = []
    total_income = Decimal("0")
    total_expense = Decimal("0")

    for acct_type, code, name, dr, cr in rows:
        t = acct_type.value if hasattr(acct_type, "value") else str(acct_type)
        amount = Decimal(str(cr)) - Decimal(str(dr)) if t == "income" else Decimal(str(dr)) - Decimal(str(cr))
        entry = {"code": code, "name": name, "amount": amount}
        if t == "income":
            income_rows.append(entry)
            total_income += amount
        else:
            expense_rows.append(entry)
            total_expense += amount

    return {
        "from_date": from_date,
        "to_date": to_date,
        "income": income_rows,
        "total_income": total_income,
        "expenses": expense_rows,
        "total_expenses": total_expense,
        "net_profit": total_income - total_expense,
    }


def balance_sheet(
    as_of: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    """Assets, Liabilities, Equity snapshot."""
    q = (
        db.query(
            Account.type,
            Account.code,
            Account.name,
            func.coalesce(func.sum(JournalLine.dr_amount), 0).label("total_dr"),
            func.coalesce(func.sum(JournalLine.cr_amount), 0).label("total_cr"),
        )
        .join(JournalLine, JournalLine.account_id == Account.id)
        .join(JournalEntry, JournalEntry.id == JournalLine.journal_entry_id)
        .filter(Account.type.in_([AccountTypeEnum.asset, AccountTypeEnum.liability, AccountTypeEnum.equity]))
    )
    if as_of:
        q = q.filter(JournalEntry.created_at <= as_of)

    rows = q.group_by(Account.type, Account.code, Account.name).order_by(Account.type, Account.code).all()

    assets, liabilities, equity = [], [], []
    total_a, total_l, total_e = Decimal("0"), Decimal("0"), Decimal("0")

    for acct_type, code, name, dr, cr in rows:
        t = acct_type.value if hasattr(acct_type, "value") else str(acct_type)
        if t == "asset":
            bal = Decimal(str(dr)) - Decimal(str(cr))
            assets.append({"code": code, "name": name, "balance": bal})
            total_a += bal
        elif t == "liability":
            bal = Decimal(str(cr)) - Decimal(str(dr))
            liabilities.append({"code": code, "name": name, "balance": bal})
            total_l += bal
        else:
            bal = Decimal(str(cr)) - Decimal(str(dr))
            equity.append({"code": code, "name": name, "balance": bal})
            total_e += bal

    return {
        "as_of": as_of,
        "assets": assets, "total_assets": total_a,
        "liabilities": liabilities, "total_liabilities": total_l,
        "equity": equity, "total_equity": total_e,
        "is_balanced": total_a == (total_l + total_e),
    }


def member_outstanding(
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    """Combined outstanding report: deposits + loans per member."""
    members = db.query(Member).filter(Member.is_active == True).order_by(Member.id).all()

    result = []
    for m in members:
        deposits = (db.query(
            func.coalesce(func.sum(DepositAccount.current_balance), 0)
        ).filter(DepositAccount.member_id == m.id,
                 DepositAccount.status == DepositStatusEnum.active).scalar())

        loans = (db.query(
            func.coalesce(func.sum(LoanAccount.outstanding_principal), 0)
        ).filter(LoanAccount.member_id == m.id,
                 LoanAccount.status == LoanStatusEnum.active).scalar())

        shares = (db.query(
            func.coalesce(func.sum(ShareHolding.total_value), 0)
        ).filter(ShareHolding.member_id == m.id).scalar())

        overdue_emis = (db.query(func.count(LoanRepayment.id))
                        .join(LoanAccount, LoanAccount.id == LoanRepayment.loan_id)
                        .filter(LoanAccount.member_id == m.id,
                                LoanRepayment.is_paid == False,
                                LoanRepayment.due_date < date.today()).scalar())

        result.append({
            "member_id": m.id,
            "member_name": m.name,
            "phone": m.phone,
            "total_deposits": Decimal(str(deposits)),
            "total_loans": Decimal(str(loans)),
            "total_shares": Decimal(str(shares)),
            "net_position": Decimal(str(deposits)) + Decimal(str(shares)) - Decimal(str(loans)),
            "overdue_emis": overdue_emis or 0,
        })

    return {"count": len(result), "members": result}


def batch_interest(
    as_of: str | None = Query(default=None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    """Calculate and post interest for ALL active deposit accounts."""
    from app.api.deposits import calculate_interest as calc_single
    from app.api.deposits import _get_or_create_system_account, _post_journal
    from app.api.deposits import INTEREST_EXPENSE_CODE

    calc_date = date.fromisoformat(as_of) if as_of else date.today()

    active_deposits = (db.query(DepositAccount)
                       .filter(DepositAccount.status == DepositStatusEnum.active)
                       .all())

    results = []
    errors = []
    from app.models.scheme import Scheme

    for dep in active_deposits:
        scheme = db.query(Scheme).filter(Scheme.id == dep.scheme_id).first()
        if not scheme:
            continue

        from_date = dep.last_interest_date or dep.opened_date
        if calc_date <= from_date:
            continue

        days = (calc_date - from_date).days
        rate = Decimal(str(scheme.interest_rate))
        interest = (dep.current_balance * rate * days / (Decimal("365") * Decimal("100"))).quantize(
            Decimal("0.01"), rounding=Decimal("0.01").__class__("0.01"))

        if interest <= 0:
            continue

        try:
            from decimal import ROUND_HALF_UP
            interest = (dep.current_balance * rate * days / (Decimal("365") * Decimal("100"))).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP)

            int_exp = _get_or_create_system_account(db, INTEREST_EXPENSE_CODE, "Interest Expense",
                                                     AccountTypeEnum.expense)
            entry = _post_journal(db, "interest_credit",
                                  f"Batch interest on {dep.account_number} for {days} days @ {rate}%",
                                  int_exp.id, dep.ledger_account_id, interest, current.user_id)

            dep.interest_earned += interest
            dep.current_balance += interest
            dep.last_interest_date = calc_date

            results.append({
                "deposit_id": dep.id,
                "account_number": dep.account_number,
                "days": days,
                "interest": interest,
            })
        except Exception as e:
            errors.append({"deposit_id": dep.id, "error": str(e)})

    db.commit()
    return {
        "processed": len(results),
        "errors": len(errors),
        "as_of": str(calc_date),
        "results": results,
        "error_details": errors,
    }


def cash_flow(
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    """Cash flow summary grouped by transaction type."""
    cash_acct = db.query(Account).filter(Account.code == "CASH-001").first()
    if not cash_acct:
        return {"inflows": [], "outflows": [], "total_inflow": 0, "total_outflow": 0, "net_flow": 0}

    q = (
        db.query(
            JournalEntry.txn_type,
            func.sum(JournalLine.dr_amount).label("total_dr"),
            func.sum(JournalLine.cr_amount).label("total_cr"),
        )
        .join(JournalEntry, JournalEntry.id == JournalLine.journal_entry_id)
        .filter(JournalLine.account_id == cash_acct.id)
    )
    if from_date:
        q = q.filter(JournalEntry.created_at >= from_date)
    if to_date:
        q = q.filter(JournalEntry.created_at <= to_date)

    rows = q.group_by(JournalEntry.txn_type).all()

    inflows, outflows = [], []
    total_in, total_out = Decimal("0"), Decimal("0")

    for txn_type, dr, cr in rows:
        dr_val = Decimal(str(dr or 0))
        cr_val = Decimal(str(cr or 0))
        if dr_val > cr_val:
            net = dr_val - cr_val
            inflows.append({"txn_type": txn_type, "amount": net})
            total_in += net
        elif cr_val > dr_val:
            net = cr_val - dr_val
            outflows.append({"txn_type": txn_type, "amount": net})
            total_out += net

    return {
        "from_date": from_date, "to_date": to_date,
        "inflows": inflows, "total_inflow": total_in,
        "outflows": outflows, "total_outflow": total_out,
        "net_flow": total_in - total_out,
    }
