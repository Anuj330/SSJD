"""Tests for the double-entry ledger service — the financial core."""

from decimal import Decimal

import pytest

from app.models.ledger import Account, JournalLine, AccountTypeEnum
from app.services.ledger_service import get_or_create_account, post_journal


def test_get_or_create_account_is_idempotent(db):
    a1 = get_or_create_account(db, "CASH-001", "Cash", AccountTypeEnum.asset)
    a2 = get_or_create_account(db, "CASH-001", "Cash", AccountTypeEnum.asset)
    db.commit()
    assert a1.id == a2.id
    assert db.query(Account).filter(Account.code == "CASH-001").count() == 1


def test_post_journal_is_balanced(db):
    cash = get_or_create_account(db, "CASH-001", "Cash", AccountTypeEnum.asset)
    income = get_or_create_account(db, "INC-001", "Income", AccountTypeEnum.income)

    entry = post_journal(
        db, "test_txn", "balanced entry",
        dr_account_id=cash.id, cr_account_id=income.id, amount=Decimal("100.00"),
    )
    db.commit()

    lines = db.query(JournalLine).filter(JournalLine.journal_entry_id == entry.id).all()
    assert len(lines) == 2
    total_dr = sum(l.dr_amount for l in lines)
    total_cr = sum(l.cr_amount for l in lines)
    # The defining invariant of double-entry bookkeeping.
    assert total_dr == total_cr == Decimal("100.00")


def test_post_journal_generates_unique_txn_refs(db):
    cash = get_or_create_account(db, "CASH-001", "Cash", AccountTypeEnum.asset)
    income = get_or_create_account(db, "INC-001", "Income", AccountTypeEnum.income)
    e1 = post_journal(db, "t", "a", cash.id, income.id, Decimal("1.00"))
    e2 = post_journal(db, "t", "b", cash.id, income.id, Decimal("2.00"))
    db.commit()
    assert e1.txn_ref != e2.txn_ref


def test_journal_line_rejects_both_sides_populated(db):
    """The DB check constraint must forbid a line with both dr and cr > 0."""
    from sqlalchemy.exc import IntegrityError

    cash = get_or_create_account(db, "CASH-001", "Cash", AccountTypeEnum.asset)
    income = get_or_create_account(db, "INC-001", "Income", AccountTypeEnum.income)
    entry = post_journal(db, "t", "x", cash.id, income.id, Decimal("5.00"))
    db.flush()

    db.add(JournalLine(
        journal_entry_id=entry.id, account_id=cash.id,
        dr_amount=Decimal("5.00"), cr_amount=Decimal("5.00"),
    ))
    with pytest.raises(IntegrityError):
        db.flush()
