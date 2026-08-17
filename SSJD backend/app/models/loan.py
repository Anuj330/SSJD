import enum

from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    Text,
    Enum,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base
from .base import TimestampMixin


class LoanTypeEnum(enum.Enum):
    personal = "personal"
    emergency = "emergency"
    gold = "gold"
    property = "property"
    agriculture = "agriculture"
    education = "education"


class RepaymentFreqEnum(enum.Enum):
    monthly = "monthly"
    quarterly = "quarterly"
    half_yearly = "half_yearly"
    yearly = "yearly"
    bullet = "bullet"  # lump sum at end


class LoanStatusEnum(enum.Enum):
    applied = "applied"
    approved = "approved"
    rejected = "rejected"
    disbursed = "disbursed"
    active = "active"          # repayment in progress
    closed = "closed"
    defaulted = "defaulted"


class LoanProduct(Base, TimestampMixin):
    """Loan product/scheme configuration."""
    __tablename__ = "loan_products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), unique=True, nullable=False)
    loan_type = Column(Enum(LoanTypeEnum, name="loan_type_enum"), nullable=False)
    description = Column(Text, nullable=True)

    interest_rate = Column(Numeric(5, 2), nullable=False)       # annual %
    min_amount = Column(Numeric(14, 2), nullable=False, default=0)
    max_amount = Column(Numeric(14, 2), nullable=True)
    max_tenure_months = Column(Integer, nullable=False, default=60)
    repayment_freq = Column(
        Enum(RepaymentFreqEnum, name="repayment_freq_enum"),
        nullable=False,
        default=RepaymentFreqEnum.monthly,
    )
    late_penalty_pct = Column(Numeric(5, 2), nullable=False, default=0)
    processing_fee_pct = Column(Numeric(5, 2), nullable=False, default=0)

    is_active = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint("interest_rate >= 0", name="ck_loan_prod_rate_non_neg"),
        CheckConstraint("min_amount >= 0", name="ck_loan_prod_min_non_neg"),
        CheckConstraint("max_tenure_months > 0", name="ck_loan_prod_tenure_pos"),
        CheckConstraint("late_penalty_pct >= 0", name="ck_loan_prod_penalty_non_neg"),
        CheckConstraint("processing_fee_pct >= 0", name="ck_loan_prod_fee_non_neg"),
    )


class LoanAccount(Base, TimestampMixin):
    """Individual loan issued to a member."""
    __tablename__ = "loan_accounts"

    id = Column(Integer, primary_key=True, index=True)
    loan_number = Column(String(30), unique=True, nullable=False, index=True)

    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("loan_products.id"), nullable=False, index=True)
    ledger_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True, index=True)

    applied_amount = Column(Numeric(14, 2), nullable=False)
    sanctioned_amount = Column(Numeric(14, 2), nullable=True)
    disbursed_amount = Column(Numeric(14, 2), nullable=False, default=0)
    outstanding_principal = Column(Numeric(14, 2), nullable=False, default=0)
    total_interest_paid = Column(Numeric(14, 2), nullable=False, default=0)
    total_penalty_paid = Column(Numeric(14, 2), nullable=False, default=0)

    tenure_months = Column(Integer, nullable=False)
    interest_rate = Column(Numeric(5, 2), nullable=False)  # locked at approval

    applied_date = Column(Date, nullable=False)
    approved_date = Column(Date, nullable=True)
    disbursed_date = Column(Date, nullable=True)
    maturity_date = Column(Date, nullable=True)
    closed_date = Column(Date, nullable=True)

    status = Column(
        Enum(LoanStatusEnum, name="loan_status_enum"),
        nullable=False,
        default=LoanStatusEnum.applied,
    )
    remarks = Column(Text, nullable=True)

    approved_by = Column(Integer, nullable=True)

    # Relationships
    member = relationship("Member")
    product = relationship("LoanProduct")
    ledger_account = relationship("Account")
    repayments = relationship("LoanRepayment", back_populates="loan", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("applied_amount > 0", name="ck_loan_applied_pos"),
        CheckConstraint("outstanding_principal >= 0", name="ck_loan_outstanding_non_neg"),
    )


class LoanRepayment(Base, TimestampMixin):
    """EMI schedule row / actual repayment record."""
    __tablename__ = "loan_repayments"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loan_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    installment_no = Column(Integer, nullable=False)

    due_date = Column(Date, nullable=False)
    principal_due = Column(Numeric(14, 2), nullable=False, default=0)
    interest_due = Column(Numeric(14, 2), nullable=False, default=0)
    total_due = Column(Numeric(14, 2), nullable=False, default=0)

    principal_paid = Column(Numeric(14, 2), nullable=False, default=0)
    interest_paid = Column(Numeric(14, 2), nullable=False, default=0)
    penalty_paid = Column(Numeric(14, 2), nullable=False, default=0)
    total_paid = Column(Numeric(14, 2), nullable=False, default=0)

    paid_date = Column(Date, nullable=True)
    is_paid = Column(Boolean, nullable=False, default=False)
    is_overdue = Column(Boolean, nullable=False, default=False)

    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True)

    loan = relationship("LoanAccount", back_populates="repayments")

    __table_args__ = (
        CheckConstraint("installment_no > 0", name="ck_repay_inst_pos"),
        CheckConstraint("principal_due >= 0", name="ck_repay_princ_due_non_neg"),
        CheckConstraint("interest_due >= 0", name="ck_repay_int_due_non_neg"),
    )


import uuid as _uuid


def gen_loan_txn_id():
    """Human-readable unique reference for a loan transaction, e.g. LNTXN-9A02FE1C3D."""
    return f"LNTXN-{_uuid.uuid4().hex[:10].upper()}"


class LoanTransaction(Base, TimestampMixin):
    """Append-only loan payment record (e.g. repayment / overdue payment).

    Created by the legacy transaction import (OD column). Not tied to a specific
    loan account when the source data has no loan reference.
    """
    __tablename__ = "loan_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(40), nullable=False, unique=True, index=True, default=gen_loan_txn_id)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    loan_id = Column(Integer, ForeignKey("loan_accounts.id"), nullable=True, index=True)
    txn_type = Column(String(40), nullable=False, default="loan_repayment")
    amount = Column(Numeric(14, 2), nullable=False)
    txn_date = Column(Date, nullable=False)
    reference_month = Column(Date, nullable=True)
    voucher_no = Column(String(40), nullable=True, index=True)
    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True)
    remarks = Column(Text, nullable=True)

    member = relationship("Member")

    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_loan_txn_amount_non_neg"),
        UniqueConstraint("member_id", "voucher_no", name="uq_loan_txn_member_voucher"),
    )
