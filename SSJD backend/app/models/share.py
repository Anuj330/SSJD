import enum

from sqlalchemy import (
    Boolean, Column, Integer, String, Date, DateTime, ForeignKey, Numeric, Enum, Text, CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base
from .base import TimestampMixin


class ShareTransactionTypeEnum(enum.Enum):
    purchase = "purchase"
    transfer = "transfer"
    refund = "refund"
    dividend = "dividend"


class ShareHolding(Base, TimestampMixin):
    """Tracks share capital held by each member."""
    __tablename__ = "share_holdings"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    total_shares = Column(Integer, nullable=False, default=0)
    face_value_per_share = Column(Numeric(14, 2), nullable=False, default=10)
    total_value = Column(Numeric(14, 2), nullable=False, default=0)

    member = relationship("Member")

    __table_args__ = (
        CheckConstraint("total_shares >= 0", name="ck_share_total_non_neg"),
    )


class ShareTransaction(Base, TimestampMixin):
    """Individual share purchase/transfer/refund transactions."""
    __tablename__ = "share_transactions"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    txn_type = Column(Enum(ShareTransactionTypeEnum, name="share_txn_type_enum"), nullable=False)
    shares = Column(Integer, nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    txn_date = Column(Date, nullable=False)
    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True)
    remarks = Column(Text, nullable=True)

    member = relationship("Member")


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
