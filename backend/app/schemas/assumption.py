"""Schemas for assumption versions."""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class RiskLevelEnum(str, Enum):
    """Risk level enum."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AssumptionCreate(BaseModel):
    """Create a new assumption version."""
    name: str = Field(..., max_length=255)
    income_growth_rate: Decimal = Field(Decimal("0.0"), ge=-50, le=50)
    expense_inflation_rate: Decimal = Field(Decimal("0.0"), ge=-50, le=50)
    investment_return_rate: Decimal = Field(Decimal("0.0"), ge=-50, le=50)
    volatility: Decimal = Field(Decimal("0.0"), ge=0, le=50)
    risk_level: RiskLevelEnum = RiskLevelEnum.MEDIUM
    notes: Optional[str] = Field(None, max_length=500)


class AssumptionResponse(BaseModel):
    """Assumption version response."""
    id: int
    user_id: int
    name: str
    version: int
    income_growth_rate: Decimal
    expense_inflation_rate: Decimal
    investment_return_rate: Decimal
    volatility: Decimal
    risk_level: RiskLevelEnum
    notes: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
