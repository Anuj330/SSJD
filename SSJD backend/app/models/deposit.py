import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    Enum,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base
from .base import TimestampMixin


class DepositStatusEnum(enum.Enum):
    active = "active"
    matured = "matured"
    closed = "closed"
    premature_closed = "premature_closed"


class DepositAccount(Base, TimestampMixin):
    __tablename__ = "deposit_accounts"

    id = Column(Integer, primary_key=True, index=True)
    account_number = Column(String(30), unique=True, nullable=False, index=True)

    member_id = Column(
        Integer, ForeignKey("members.id"), nullable=False, index=True
    )
    scheme_id = Column(
        Integer, ForeignKey("schemes.id"), nullable=False, index=True
    )
    ledger_account_id = Column(
        Integer, ForeignKey("accounts.id"), nullable=False, index=True
    )

    principal_amount = Column(Numeric(14, 2), nullable=False, default=0)
    current_balance = Column(Numeric(14, 2), nullable=False, default=0)
    interest_earned = Column(Numeric(14, 2), nullable=False, default=0)

    opened_date = Column(Date, nullable=False)
    maturity_date = Column(Date, nullable=True)  # NULL for savings
    last_interest_date = Column(Date, nullable=True)

    status = Column(
        Enum(DepositStatusEnum, name="deposit_status_enum"),
        nullable=False,
        default=DepositStatusEnum.active,
    )

    closed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    member = relationship("Member")
    scheme = relationship("Scheme")
    ledger_account = relationship("Account")

    __table_args__ = (
        CheckConstraint(
            "principal_amount >= 0", name="ck_deposit_principal_non_negative"
        ),
        CheckConstraint(
            "current_balance >= 0", name="ck_deposit_balance_non_negative"
        ),
        CheckConstraint(
            "interest_earned >= 0", name="ck_deposit_interest_non_negative"
        ),
    )
