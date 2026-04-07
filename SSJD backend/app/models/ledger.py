from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Numeric,
    CheckConstraint,
    Enum,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from ..core.database import Base


class AccountTypeEnum(enum.Enum):
    asset = "asset"
    liability = "liability"
    income = "income"
    expense = "expense"
    equity = "equity"


class OwnerTypeEnum(enum.Enum):
    society = "society"
    member = "member"
    system = "system"


class EntryStatusEnum(enum.Enum):
    posted = "posted"
    reversed = "reversed"


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False)
    type = Column(Enum(AccountTypeEnum, name="account_type_enum"), nullable=False)

    owner_type = Column(Enum(OwnerTypeEnum, name="owner_type_enum"), nullable=False)
    owner_id = Column(Integer, nullable=True, index=True)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    txn_ref = Column(String(100), unique=True, nullable=False, index=True)
    txn_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)

    status = Column(Enum(EntryStatusEnum, name="entry_status_enum"), nullable=False, default=EntryStatusEnum.posted)

    reversed_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    lines = relationship("JournalLine", back_populates="entry", cascade="all, delete-orphan")


class JournalLine(Base):
    __tablename__ = "journal_lines"

    id = Column(Integer, primary_key=True, index=True)
    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)

    dr_amount = Column(Numeric(14, 2), nullable=False, default=0)
    cr_amount = Column(Numeric(14, 2), nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="INR")
    line_note = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account")

    __table_args__ = (
        CheckConstraint("dr_amount >= 0", name="ck_journal_lines_dr_non_negative"),
        CheckConstraint("cr_amount >= 0", name="ck_journal_lines_cr_non_negative"),
        CheckConstraint(
            "(dr_amount = 0 AND cr_amount > 0) OR (cr_amount = 0 AND dr_amount > 0)",
            name="ck_journal_lines_one_side_only",
        ),
    )
