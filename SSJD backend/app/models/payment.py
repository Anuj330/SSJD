"""Razorpay payment order tracking."""

from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, ForeignKey, Enum as SAEnum,
)
from sqlalchemy.sql import func
import enum

from ..core.database import Base


class PaymentStatusEnum(str, enum.Enum):
    created = "created"
    paid = "paid"
    failed = "failed"
    refunded = "refunded"


class PaymentOrder(Base):
    __tablename__ = "payment_orders"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)

    # What this payment is for
    purpose = Column(String(50), nullable=False)  # deposit, loan_repayment, share_purchase, rd_installment
    entity_id = Column(Integer, nullable=True)     # deposit_id, loan_id, etc.

    amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(3), default="INR")

    # Razorpay fields
    razorpay_order_id = Column(String(100), unique=True, index=True)
    razorpay_payment_id = Column(String(100), nullable=True)
    razorpay_signature = Column(String(256), nullable=True)

    status = Column(SAEnum(PaymentStatusEnum), default=PaymentStatusEnum.created, nullable=False)
    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
