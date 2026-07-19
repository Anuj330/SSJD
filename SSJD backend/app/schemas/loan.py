from decimal import Decimal
from typing import Optional, List
from datetime import date, datetime

from pydantic import BaseModel, Field


# ─── Loan Product ───

class LoanProductCreate(BaseModel):
    name: str
    loan_type: str
    description: Optional[str] = None
    interest_rate: Decimal = Field(ge=0)
    min_amount: Decimal = Field(ge=0, default=Decimal("0"))
    max_amount: Optional[Decimal] = None
    max_tenure_months: int = Field(gt=0, default=60)
    repayment_freq: str = "monthly"
    late_penalty_pct: Decimal = Field(ge=0, default=Decimal("0"))
    processing_fee_pct: Decimal = Field(ge=0, default=Decimal("0"))


class LoanProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    interest_rate: Optional[Decimal] = Field(default=None, ge=0)
    min_amount: Optional[Decimal] = Field(default=None, ge=0)
    max_amount: Optional[Decimal] = None
    max_tenure_months: Optional[int] = Field(default=None, gt=0)
    repayment_freq: Optional[str] = None
    late_penalty_pct: Optional[Decimal] = Field(default=None, ge=0)
    processing_fee_pct: Optional[Decimal] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class LoanProductResponse(BaseModel):
    id: int
    name: str
    loan_type: str
    description: Optional[str]
    interest_rate: Decimal
    min_amount: Decimal
    max_amount: Optional[Decimal]
    max_tenure_months: int
    repayment_freq: str
    late_penalty_pct: Decimal
    processing_fee_pct: Decimal
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Loan Application ───

class LoanApplyRequest(BaseModel):
    member_id: int
    product_id: int
    amount: Decimal = Field(gt=0)
    tenure_months: int = Field(gt=0)
    remarks: Optional[str] = None


class LoanApproveRequest(BaseModel):
    sanctioned_amount: Optional[Decimal] = Field(default=None, gt=0)
    remarks: Optional[str] = None


class LoanRepaymentRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    description: Optional[str] = None
    payment_date: Optional[str] = None  # YYYY-MM-DD (default: today)


# ─── Response Models ───

class RepaymentScheduleRow(BaseModel):
    installment_no: int
    due_date: date
    principal_due: Decimal
    interest_due: Decimal
    total_due: Decimal
    principal_paid: Decimal
    interest_paid: Decimal
    penalty_paid: Decimal
    total_paid: Decimal
    paid_date: Optional[date]
    is_paid: bool
    is_overdue: bool


class LoanAccountResponse(BaseModel):
    id: int
    loan_number: str
    member_id: int
    product_id: int
    applied_amount: Decimal
    sanctioned_amount: Optional[Decimal]
    disbursed_amount: Decimal
    outstanding_principal: Decimal
    total_interest_paid: Decimal
    total_penalty_paid: Decimal
    tenure_months: int
    interest_rate: Decimal
    applied_date: date
    approved_date: Optional[date]
    disbursed_date: Optional[date]
    maturity_date: Optional[date]
    closed_date: Optional[date]
    status: str
    remarks: Optional[str]
    member_name: Optional[str] = None
    product_name: Optional[str] = None

    class Config:
        from_attributes = True
