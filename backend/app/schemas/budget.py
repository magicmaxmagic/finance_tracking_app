"""Budget schemas for request/response validation."""
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional
from decimal import Decimal


class BudgetCreate(BaseModel):
    """Schema for budget creation."""
    category_id: int
    amount: Decimal = Field(..., gt=0)
    month: date


class BudgetUpdate(BaseModel):
    """Schema for budget update."""
    amount: Optional[Decimal] = Field(None, gt=0)
    month: Optional[date] = None


class BudgetResponse(BaseModel):
    """Schema for budget response."""
    id: int
    user_id: int
    category_id: int
    amount: Decimal
    month: date
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BudgetWithSpent(BaseModel):
    """Schema for budget with spent amount."""
    id: int
    category_id: int
    category_name: str
    amount: Decimal
    spent: Decimal
    remaining: Decimal
    percentage_used: float
    month: date
