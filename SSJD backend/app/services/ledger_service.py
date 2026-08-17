"""Shared double-entry ledger helpers.

Single source of truth for creating ledger accounts and posting balanced
journal entries. Previously these were copy-pasted across deposits.py,
loans.py, and scheduler.py — divergence there risks unbalanced books.
"""

import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.ledger import (
    Account,
    JournalEntry,
    JournalLine,
    AccountTypeEnum,
    OwnerTypeEnum,
    EntryStatusEnum,
)


def get_or_create_account(
    db: Session,
    code: str,
    name: str,
    acct_type: AccountTypeEnum,
    owner_type: OwnerTypeEnum = OwnerTypeEnum.society,
    owner_id: int | None = None,
) -> Account:
    """Fetch a ledger account by code, creating it on first use."""
    acct = db.query(Account).filter(Account.code == code).first()
    if not acct:
        acct = Account(
            code=code,
            name=name,
            type=acct_type,
            owner_type=owner_type,
            owner_id=owner_id,
            is_active=True,
        )
        db.add(acct)
        db.flush()
    return acct


def post_journal(
    db: Session,
    txn_type: str,
    description: str,
    dr_account_id: int,
    cr_account_id: int,
    amount: Decimal,
    created_by: int | None = None,
) -> JournalEntry:
    """Post a balanced two-line journal entry (one debit, one credit)."""
    txn_ref = f"TXN-{uuid.uuid4().hex[:12].upper()}"
    entry = JournalEntry(
        txn_ref=txn_ref,
        txn_type=txn_type,
        description=description,
        created_by=created_by,
        status=EntryStatusEnum.posted,
    )
    db.add(entry)
    db.flush()

    db.add(JournalLine(
        journal_entry_id=entry.id,
        account_id=dr_account_id,
        dr_amount=amount,
        cr_amount=Decimal("0"),
    ))
    db.add(JournalLine(
        journal_entry_id=entry.id,
        account_id=cr_account_id,
        dr_amount=Decimal("0"),
        cr_amount=amount,
    ))
    return entry
