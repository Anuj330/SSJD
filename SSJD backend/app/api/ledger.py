from datetime import datetime
from decimal import Decimal
import uuid

from fastapi import Depends, HTTPException, Query
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_admin, get_current_account
from app.models.ledger import Account, JournalEntry, JournalLine, EntryStatusEnum, OwnerTypeEnum, AccountTypeEnum
from app.schemas.ledger import AccountCreate, AccountUpdate, JournalPostRequest


def create_account(
    payload: AccountCreate,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    # Auto-generate a unique code from the type when the admin didn't supply one
    # (e.g. ASSET-003), so accounts can be added with just a name + type.
    code = (payload.code or "").strip()
    if not code:
        prefix = str(payload.type).upper()[:6]
        n = db.query(Account).filter(Account.type == payload.type).count() + 1
        code = f"{prefix}-{n:03d}"
        while db.query(Account).filter(Account.code == code).first():
            n += 1
            code = f"{prefix}-{n:03d}"

    if db.query(Account).filter(Account.code == code).first():
        raise HTTPException(status_code=400, detail="Account code already exists")

    account = Account(
        code=code,
        name=payload.name,
        type=payload.type,
        category=(payload.category or "").strip() or None,
        owner_type=payload.owner_type or "society",
        owner_id=payload.owner_id,
        is_active=True,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def list_accounts(
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    """Full chart of accounts (incl. accounts with no transactions yet), with
    category, active flag, and running totals. Used by the Accounts admin page."""
    rows = (db.query(
                Account.id.label("id"), Account.code.label("code"),
                Account.name.label("name"), Account.type.label("type"),
                Account.category.label("category"), Account.owner_type.label("owner_type"),
                Account.is_active.label("is_active"),
                func.coalesce(func.sum(JournalLine.dr_amount), 0).label("dr"),
                func.coalesce(func.sum(JournalLine.cr_amount), 0).label("cr"))
            .outerjoin(JournalLine, JournalLine.account_id == Account.id)
            .outerjoin(JournalEntry, JournalEntry.id == JournalLine.journal_entry_id)
            .group_by(Account.id, Account.code, Account.name, Account.type,
                      Account.category, Account.owner_type, Account.is_active)
            .order_by(Account.type.asc(), Account.code.asc())
            .all())
    return [
        {
            "account_id": r.id, "account_code": r.code, "account_name": r.name,
            "account_type": r.type.value if hasattr(r.type, "value") else str(r.type),
            "category": r.category,
            "owner_type": r.owner_type.value if hasattr(r.owner_type, "value") else str(r.owner_type),
            "is_active": r.is_active,
            "total_debit": r.dr, "total_credit": r.cr,
        }
        for r in rows
    ]


def update_account(
    account_id: int,
    payload: AccountUpdate,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    """Edit an existing account's name, type, category, or active flag."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if payload.name is not None:
        account.name = payload.name.strip()
    if payload.type is not None:
        account.type = payload.type
    if payload.category is not None:
        account.category = payload.category.strip() or None
    if payload.is_active is not None:
        account.is_active = payload.is_active
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


def _account_totals(db, types=None, from_date=None, to_date=None):
    """Per-account (debit, credit) totals from posted journal lines, with
    optional account-type and date-range filters. Shared by P&L + Balance Sheet."""
    q = (db.query(
            Account.id.label("id"), Account.code.label("code"),
            Account.name.label("name"), Account.type.label("type"),
            Account.category.label("category"),
            func.coalesce(func.sum(JournalLine.dr_amount), 0).label("dr"),
            func.coalesce(func.sum(JournalLine.cr_amount), 0).label("cr"))
         .join(JournalLine, JournalLine.account_id == Account.id)
         .join(JournalEntry, JournalEntry.id == JournalLine.journal_entry_id)
         .group_by(Account.id, Account.code, Account.name, Account.type, Account.category)
         .order_by(Account.code.asc()))
    if types:
        q = q.filter(Account.type.in_(types))
    if from_date:
        q = q.filter(JournalEntry.created_at >= from_date)
    if to_date:
        q = q.filter(JournalEntry.created_at <= to_date)
    return q.all()


def profit_and_loss(
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    """Income & Expenditure statement for a period. Income is credit-natured,
    expense is debit-natured; net = income − expense (surplus if positive)."""
    rows = _account_totals(db, types=[AccountTypeEnum.income, AccountTypeEnum.expense],
                           from_date=from_date, to_date=to_date)

    def group(side_rows, default_cat):
        """Bifurcate accounts into category heads with subtotals."""
        groups = {}  # category -> {"category", "subtotal", "accounts": [...]}
        for code, name, amount, cat in side_rows:
            key = cat or default_cat
            g = groups.setdefault(key, {"category": key, "subtotal": Decimal("0"), "accounts": []})
            g["subtotal"] += amount
            g["accounts"].append({"account_code": code, "account_name": name, "amount": amount})
        return sorted(groups.values(), key=lambda x: x["category"].lower())

    income_rows, expense_rows = [], []
    total_income = total_expense = Decimal("0")
    for r in rows:
        dr, cr = Decimal(r.dr), Decimal(r.cr)
        tval = r.type.value if hasattr(r.type, "value") else str(r.type)
        if tval == "income":
            amt = cr - dr
            total_income += amt
            income_rows.append((r.code, r.name, amt, r.category))
        else:
            amt = dr - cr
            total_expense += amt
            expense_rows.append((r.code, r.name, amt, r.category))

    net = total_income - total_expense
    return {
        "from_date": from_date, "to_date": to_date,
        "income": group(income_rows, "Other Income"),
        "total_income": total_income,
        "expense": group(expense_rows, "Other Expenses"),
        "total_expense": total_expense,
        "net_profit": net,
        "result": "surplus" if net >= 0 else "deficit",
    }


def balance_sheet(
    as_of: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_admin),
):
    """Balance Sheet as of a date. Assets = Liabilities + Equity + current
    surplus/deficit (unclosed income − expense, folded into equity so it ties)."""
    rows = _account_totals(db, types=[AccountTypeEnum.asset, AccountTypeEnum.liability,
                                      AccountTypeEnum.equity], to_date=as_of)
    assets, liabilities, equity = [], [], []
    total_assets = total_liabilities = total_equity = Decimal("0")
    for r in rows:
        dr, cr = Decimal(r.dr), Decimal(r.cr)
        tval = r.type.value if hasattr(r.type, "value") else str(r.type)
        if tval == "asset":
            amt = dr - cr
            total_assets += amt
            assets.append({"account_code": r.code, "account_name": r.name, "amount": amt})
        elif tval == "liability":
            amt = cr - dr
            total_liabilities += amt
            liabilities.append({"account_code": r.code, "account_name": r.name, "amount": amt})
        else:
            amt = cr - dr
            total_equity += amt
            equity.append({"account_code": r.code, "account_name": r.name, "amount": amt})

    # Current-period surplus/deficit (income − expense) up to as_of, shown under equity.
    ie = _account_totals(db, types=[AccountTypeEnum.income, AccountTypeEnum.expense], to_date=as_of)
    inc = exp = Decimal("0")
    for r in ie:
        dr, cr = Decimal(r.dr), Decimal(r.cr)
        tval = r.type.value if hasattr(r.type, "value") else str(r.type)
        if tval == "income":
            inc += cr - dr
        else:
            exp += dr - cr
    surplus = inc - exp

    total_equity_and_surplus = total_equity + surplus
    total_liab_eq = total_liabilities + total_equity_and_surplus
    return {
        "as_of": as_of,
        "assets": assets, "total_assets": total_assets,
        "liabilities": liabilities, "total_liabilities": total_liabilities,
        "equity": equity, "total_equity": total_equity,
        "current_surplus": surplus,
        "total_liabilities_and_equity": total_liab_eq,
        "is_balanced": abs(total_assets - total_liab_eq) < Decimal("0.01"),
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

    import re
    from app.models.share import ShareTransaction

    # 1) Member-owned ledger lines (deposits, etc.)
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

    # Collect everything into (sort_date, row) so multiple sources merge into one passbook.
    items = []  # (date_obj, partial_row_dict)

    for line, entry, account in query.all():
        desc = entry.description or ""
        penalty_amount = Decimal("0")
        is_penalty = "penalty" in desc.lower()
        if is_penalty:
            m = re.search(r"penalty[:\s]+([\d,.]+)", desc, re.IGNORECASE)
            if m:
                try:
                    penalty_amount = Decimal(m.group(1).replace(",", ""))
                except Exception:
                    pass
        tt = entry.txn_type or ""
        is_loan = "loan" in tt.lower()
        disp = tt
        if is_loan:
            disp = "Loan Repayment" if "repay" in tt.lower() else (
                "Loan Disbursement" if "disburse" in tt.lower() else tt.replace("_", " ").title())
        d = entry.created_at
        items.append((d.date() if hasattr(d, "date") else d, {
            "date": entry.created_at, "txn_ref": entry.txn_ref, "txn_type": disp,
            "description": desc, "account_name": account.name,
            "debit": Decimal(line.dr_amount), "credit": Decimal(line.cr_amount),
            "penalty": penalty_amount, "is_penalty": is_penalty, "is_loan": is_loan,
        }))

    # 2) Share-money transactions (posted to the society's Share Capital account, so
    #    they don't appear as member-owned ledger lines — merge them in here).
    sq = db.query(ShareTransaction).filter(ShareTransaction.member_id == member_id)
    if from_date:
        sq = sq.filter(ShareTransaction.txn_date >= from_date.date() if hasattr(from_date, "date") else from_date)
    if to_date:
        sq = sq.filter(ShareTransaction.txn_date <= to_date.date() if hasattr(to_date, "date") else to_date)
    for st in sq.all():
        amt = Decimal(st.amount)
        is_wd = str(st.txn_type).lower() == "withdrawal"
        label = {"monthly_share_deposit": "Share Deposit", "withdrawal": "Share Withdrawal",
                 "dividend": "Dividend"}.get(str(st.txn_type).lower(), str(st.txn_type))
        items.append((st.txn_date, {
            "date": st.txn_date, "txn_ref": st.transaction_id, "txn_type": label,
            "description": st.remarks or "Share money", "account_name": "Share Money",
            "debit": amt if is_wd else Decimal("0"), "credit": Decimal("0") if is_wd else amt,
            "penalty": Decimal("0"), "is_penalty": False, "is_loan": False,
        }))

    # 3) Loan payments recorded in the dedicated loan_transactions table.
    from app.models.loan import LoanTransaction
    lq = db.query(LoanTransaction).filter(LoanTransaction.member_id == member_id)
    if from_date:
        lq = lq.filter(LoanTransaction.txn_date >= (from_date.date() if hasattr(from_date, "date") else from_date))
    if to_date:
        lq = lq.filter(LoanTransaction.txn_date <= (to_date.date() if hasattr(to_date, "date") else to_date))
    for lt in lq.all():
        items.append((lt.txn_date, {
            "date": lt.txn_date, "txn_ref": lt.transaction_id, "txn_type": "Loan Repayment",
            "description": lt.remarks or "Loan repayment", "account_name": "Loan",
            "debit": Decimal(lt.amount), "credit": Decimal("0"),
            "penalty": Decimal("0"), "is_penalty": False, "is_loan": True,
        }))

    # Merge by date (stable), then compute the running balance over the full statement.
    items.sort(key=lambda x: (x[0] is None, x[0]))

    result = []
    running_balance = Decimal("0")
    total_credited = Decimal("0")
    total_debited = Decimal("0")
    total_penalty = Decimal("0")
    total_loan_paid = Decimal("0")
    for _, row in items:
        if row.get("is_loan"):
            # Loan payments are listed but don't change the savings/share balance.
            total_loan_paid += row["debit"] + row["credit"]
            row["running_balance"] = running_balance
        else:
            total_credited += row["credit"]
            total_debited += row["debit"]
            total_penalty += row["penalty"]
            running_balance += row["credit"] - row["debit"]
            row["running_balance"] = running_balance
        result.append(row)

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
        "total_loan_paid": total_loan_paid,
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
