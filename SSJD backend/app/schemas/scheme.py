from decimal import Decimal
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class SchemeCreate(BaseModel):
    name: str
    scheme_type: str  # fd, rd, mis, savings
    description: Optional[str] = None
    interest_rate: Decimal = Field(ge=0)
    min_amount: Decimal = Field(ge=0, default=Decimal("0"))
    max_amount: Optional[Decimal] = None
    tenure_months: Optional[int] = Field(default=None, gt=0)
    compounding: str = "quarterly"
    premature_penalty_pct: Decimal = Field(ge=0, default=Decimal("0"))


class SchemeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    interest_rate: Optional[Decimal] = Field(default=None, ge=0)
    min_amount: Optional[Decimal] = Field(default=None, ge=0)
    max_amount: Optional[Decimal] = None
    tenure_months: Optional[int] = Field(default=None, gt=0)
    compounding: Optional[str] = None
    premature_penalty_pct: Optional[Decimal] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class SchemeResponse(BaseModel):
    id: int
    name: str
    scheme_type: str
    description: Optional[str]
    interest_rate: Decimal
    min_amount: Decimal
    max_amount: Optional[Decimal]
    tenure_months: Optional[int]
    compounding: str
    premature_penalty_pct: Decimal
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
