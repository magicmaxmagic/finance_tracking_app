"""Schemas for onboarding profiles."""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class RiskAppetiteEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class InvestorProfileEnum(str, Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    GROWTH = "growth"
    ACTIVE = "active"


class OnboardingProfileCreate(BaseModel):
    risk_appetite: RiskAppetiteEnum
    investor_profile: InvestorProfileEnum
    goal_value: Decimal = Field(..., gt=0)
    goal_horizon_years: int = Field(..., ge=1, le=40)
    asset_allocation: List[str]
    investment_interests: List[str]
    vision: Optional[str] = Field(None, max_length=500)


class OnboardingProfileResponse(BaseModel):
    id: int
    user_id: int
    risk_appetite: RiskAppetiteEnum
    investor_profile: InvestorProfileEnum
    goal_value: Decimal
    goal_horizon_years: int
    target_date: date
    asset_allocation: List[str]
    investment_interests: List[str]
    vision: Optional[str]
    is_completed: bool
    completed_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OnboardingStatus(BaseModel):
    is_completed: bool
