import uuid

from sqlalchemy import (
    Column, Integer, String, Date, ForeignKey, Numeric, Text, CheckConstraint,
)
from sqlalchemy.orm import relationship

from ..core.database import Base
from .base import TimestampMixin


# Advance-wallet movement types (stored as strings):
ADVANCE_CREDIT = "credit"   # money parked into the wallet (surplus from a collection)
ADVANCE_DEBIT = "debit"     # money drawn from the wallet (applied to an EMI / share, etc.)


def gen_advance_txn_id():
    """Human-readable unique reference, e.g. ADV-9A02FE1C3D."""
    return f"ADV-{uuid.uuid4().hex[:10].upper()}"


class MemberAdvance(Base, TimestampMixin):
    """A member's advance / adjust-balance wallet — a running held-credit balance."""
    __tablename__ = "member_advances"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, unique=True, index=True)
    balance = Column(Numeric(14, 2), nullable=False, default=0)

    member = relationship("Member")

    __table_args__ = (
        CheckConstraint("balance >= 0", name="ck_advance_balance_non_neg"),
    )


class AdvanceTransaction(Base, TimestampMixin):
    """A single advance-wallet movement (credit = parked, debit = applied)."""
    __tablename__ = "advance_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(40), nullable=False, unique=True, index=True, default=gen_advance_txn_id)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    txn_type = Column(String(20), nullable=False, default=ADVANCE_CREDIT)
    amount = Column(Numeric(14, 2), nullable=False)
    txn_date = Column(Date, nullable=False)
    reference = Column(String(120), nullable=True)   # what it relates to (e.g. "Collection", "Applied to EMI")
    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True)
    remarks = Column(Text, nullable=True)

    member = relationship("Member")
