"""Schemas for scenario modeling."""
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class ActionTypeEnum(str, Enum):
    """Action types for scenarios."""
    INCOME_DELTA = "income_delta"
    EXPENSE_DELTA = "expense_delta"
    INVESTMENT_DELTA = "investment_delta"
    ONE_TIME_INVESTMENT = "one_time_investment"


class ScenarioActionCreate(BaseModel):
    """Create a scenario action."""
    action_type: ActionTypeEnum
    value: Decimal
    start_date: date
    end_date: Optional[date] = None


class ScenarioActionResponse(BaseModel):
    """Scenario action response."""
    id: int
    action_type: ActionTypeEnum
    value: Decimal
    start_date: date
    end_date: Optional[date]
    created_at: datetime

    class Config:
        from_attributes = True


class ScenarioCreate(BaseModel):
    """Create scenario."""
    name: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    goal_id: Optional[int] = None
    assumption_id: Optional[int] = None
    is_baseline: bool = False
    scenario_group_id: Optional[str] = None
    actions: List[ScenarioActionCreate] = []


class ScenarioUpdate(BaseModel):
    """Create a new scenario version."""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    goal_id: Optional[int] = None
    assumption_id: Optional[int] = None
    is_baseline: Optional[bool] = None
    actions: Optional[List[ScenarioActionCreate]] = None


class ScenarioResponse(BaseModel):
    """Scenario response."""
    id: int
    user_id: int
    goal_id: Optional[int]
    assumption_id: Optional[int]
    name: str
    description: Optional[str]
    scenario_group_id: str
    version: int
    is_baseline: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    actions: List[ScenarioActionResponse] = []

    class Config:
        from_attributes = True
