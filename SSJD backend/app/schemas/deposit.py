from decimal import Decimal
from typing import Optional
from datetime import date, datetime

from pydantic import BaseModel, Field


class DepositOpenRequest(BaseModel):
    member_id: int
    scheme_id: int
    amount: Decimal = Field(gt=0)
    opened_date: Optional[date] = None  # defaults to today


class DepositTransactionRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    description: Optional[str] = None


class DepositResponse(BaseModel):
    id: int
    account_number: str
    member_id: int
    scheme_id: int
    ledger_account_id: int
    principal_amount: Decimal
    current_balance: Decimal
    interest_earned: Decimal
    opened_date: date
    maturity_date: Optional[date]
    last_interest_date: Optional[date]
    status: str
    created_at: Optional[datetime] = None

    # Joined fields (populated in list/detail responses)
    member_name: Optional[str] = None
    scheme_name: Optional[str] = None

    class Config:
        from_attributes = True


class DepositStatementRow(BaseModel):
    entry_id: int
    txn_ref: str
    txn_type: str
    created_at: datetime
    dr_amount: Decimal
    cr_amount: Decimal
    description: Optional[str]


class InterestCalculationResult(BaseModel):
    deposit_id: int
    account_number: str
    days: int
    rate: Decimal
    interest_amount: Decimal
    journal_entry_id: int
