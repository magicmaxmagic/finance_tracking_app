"""Schemas for financial goals."""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class GoalTypeEnum(str, Enum):
    """Goal types."""
    NET_WORTH = "net_worth"
    LIQUID_ASSETS = "liquid_assets"


class GoalStatusEnum(str, Enum):
    """Goal status values."""
    ACTIVE = "active"
    ACHIEVED = "achieved"
    ARCHIVED = "archived"


class FinancialGoalCreate(BaseModel):
    """Create a new financial goal."""
    name: str = Field(..., max_length=255)
    target_type: GoalTypeEnum
    target_value: Decimal = Field(..., gt=0)
    target_date: date


class FinancialGoalUpdate(BaseModel):
    """Update financial goal."""
    name: Optional[str] = Field(None, max_length=255)
    target_value: Optional[Decimal] = Field(None, gt=0)
    target_date: Optional[date] = None
    status: Optional[GoalStatusEnum] = None


class FinancialGoalResponse(BaseModel):
    """Financial goal response schema."""
    id: int
    user_id: int
    name: str
    target_type: GoalTypeEnum
    target_value: Decimal
    target_date: date
    status: GoalStatusEnum
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
