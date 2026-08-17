import enum

from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    Numeric,
    Enum,
    Text,
    CheckConstraint,
)

from ..core.database import Base
from .base import TimestampMixin


class SchemeTypeEnum(enum.Enum):
    fd = "fd"           # Fixed Deposit
    rd = "rd"           # Recurring Deposit
    mis = "mis"         # Monthly Income Scheme
    savings = "savings" # Savings Account


class CompoundingEnum(enum.Enum):
    monthly = "monthly"
    quarterly = "quarterly"
    half_yearly = "half_yearly"
    yearly = "yearly"
    on_maturity = "on_maturity"


class Scheme(Base, TimestampMixin):
    __tablename__ = "schemes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), unique=True, nullable=False)
    scheme_type = Column(
        Enum(SchemeTypeEnum, name="scheme_type_enum"), nullable=False
    )
    description = Column(Text, nullable=True)

    interest_rate = Column(Numeric(5, 2), nullable=False)  # e.g. 7.50%
    min_amount = Column(Numeric(14, 2), nullable=False, default=0)
    max_amount = Column(Numeric(14, 2), nullable=True)      # NULL = no upper limit
    tenure_months = Column(Integer, nullable=True)           # NULL for savings

    compounding = Column(
        Enum(CompoundingEnum, name="compounding_enum"),
        nullable=False,
        default=CompoundingEnum.quarterly,
    )
    premature_penalty_pct = Column(Numeric(5, 2), nullable=False, default=0)

    is_active = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint("interest_rate >= 0", name="ck_scheme_rate_non_negative"),
        CheckConstraint("min_amount >= 0", name="ck_scheme_min_non_negative"),
        CheckConstraint(
            "max_amount IS NULL OR max_amount >= min_amount",
            name="ck_scheme_max_gte_min",
        ),
        CheckConstraint(
            "tenure_months IS NULL OR tenure_months > 0",
            name="ck_scheme_tenure_positive",
        ),
        CheckConstraint(
            "premature_penalty_pct >= 0",
            name="ck_scheme_penalty_non_negative",
        ),
    )
