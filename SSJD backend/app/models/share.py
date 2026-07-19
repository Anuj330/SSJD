import enum
import uuid

from sqlalchemy import (
    Boolean, Column, Integer, String, Date, DateTime, ForeignKey, Numeric, Enum, Text,
    CheckConstraint, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base
from .base import TimestampMixin


# Share money is plain money a member stores with the society (like a bank account).
# Transaction types (stored as strings):
SHARE_DEPOSIT = "monthly_share_deposit"
SHARE_WITHDRAWAL = "withdrawal"
SHARE_DIVIDEND = "dividend"


def gen_share_txn_id():
    """Human-readable unique reference for a share transaction, e.g. SHTXN-9A02FE1C3D."""
    return f"SHTXN-{uuid.uuid4().hex[:10].upper()}"


class ShareHolding(Base, TimestampMixin):
    """A member's share-money account — just a running balance."""
    __tablename__ = "share_holdings"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    balance = Column(Numeric(14, 2), nullable=False, default=0)   # SM total = cd + od
    cd_balance = Column(Numeric(14, 2), nullable=False, default=0)  # Compulsory Deposit
    od_balance = Column(Numeric(14, 2), nullable=False, default=0)  # Optional Deposit

    member = relationship("Member")

    __table_args__ = (
        CheckConstraint("balance >= 0", name="ck_share_balance_non_neg"),
    )


class ShareTransaction(Base, TimestampMixin):
    """A single share-money movement (deposit / withdrawal / dividend)."""
    __tablename__ = "share_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(40), nullable=False, unique=True, index=True, default=gen_share_txn_id)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    txn_type = Column(String(40), nullable=False, default=SHARE_DEPOSIT)
    amount = Column(Numeric(14, 2), nullable=False)          # SM = cd_amount + od_amount
    cd_amount = Column(Numeric(14, 2), nullable=False, default=0)
    od_amount = Column(Numeric(14, 2), nullable=False, default=0)
    txn_date = Column(Date, nullable=False)
    reference_month = Column(Date, nullable=True)          # 1st of the contribution month
    voucher_no = Column(String(40), nullable=True, index=True)  # source voucher (legacy imports)
    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True)
    remarks = Column(Text, nullable=True)

    member = relationship("Member")

    __table_args__ = (
        # One share entry per (member, voucher) — guards legacy re-imports.
        UniqueConstraint("member_id", "voucher_no", name="uq_share_txn_member_voucher"),
    )


class RDInstallment(Base, TimestampMixin):
    """Tracks recurring deposit monthly installments."""
    __tablename__ = "rd_installments"

    id = Column(Integer, primary_key=True, index=True)
    deposit_account_id = Column(Integer, ForeignKey("deposit_accounts.id"), nullable=False, index=True)
    installment_no = Column(Integer, nullable=False)

    due_date = Column(Date, nullable=False)
    amount_due = Column(Numeric(14, 2), nullable=False)
    amount_paid = Column(Numeric(14, 2), nullable=False, default=0)
    penalty = Column(Numeric(14, 2), nullable=False, default=0)

    paid_date = Column(Date, nullable=True)
    is_paid = Column(Boolean, nullable=False, default=False)
    is_overdue = Column(Boolean, nullable=False, default=False)

    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True)

    deposit_account = relationship("DepositAccount")

    __table_args__ = (
        CheckConstraint("installment_no > 0", name="ck_rd_inst_pos"),
        CheckConstraint("amount_due >= 0", name="ck_rd_amount_due_non_neg"),
    )
