from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class AccountCreate(BaseModel):
    code: str
    name: str
    type: str
    owner_type: str
    owner_id: Optional[int] = None


class AccountResponse(BaseModel):
    id: int
    code: str
    name: str
    type: str
    owner_type: str
    owner_id: Optional[int]

    class Config:
        from_attributes = True


class JournalLineInput(BaseModel):
    account_id: int
    dr_amount: Decimal = Decimal("0")
    cr_amount: Decimal = Decimal("0")
    currency: str = "INR"
    line_note: Optional[str] = None


class JournalPostRequest(BaseModel):
    txn_ref: Optional[str] = None
    txn_type: str
    description: Optional[str] = None
    created_by: Optional[int] = None
    lines: List[JournalLineInput]


class JournalPostResponse(BaseModel):
    id: int
    txn_ref: str
    status: str
    total_debit: Decimal
    total_credit: Decimal


class StatementLine(BaseModel):
    entry_id: int
    txn_ref: str
    txn_type: str
    created_at: datetime
    dr_amount: Decimal
    cr_amount: Decimal
    currency: str
    line_note: Optional[str]


class TrialBalanceRow(BaseModel):
    account_id: int
    account_code: str
    account_name: str
    account_type: str
    total_debit: Decimal
    total_credit: Decimal


class MemberMoneyFlowRow(BaseModel):
    entry_id: int
    txn_ref: str
    txn_type: str
    created_at: datetime
    account_code: str
    account_name: str
    dr_amount: Decimal
    cr_amount: Decimal
