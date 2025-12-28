"""Account schemas for request/response validation."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from decimal import Decimal


class AccountTypeEnum(str):
    """Account type enum."""
    CASH = "cash"
    SAVINGS = "savings"
    CHECKING = "checking"
    CREDIT = "credit"
    INVESTMENT = "investment"
    DEBT = "debt"
    OTHER = "other"


class AccountCreate(BaseModel):
    """Schema for account creation."""
    name: str = Field(..., max_length=255)
    account_type: str
    currency: str = "USD"
    balance: Decimal = Decimal("0.00")
    description: Optional[str] = None


class AccountUpdate(BaseModel):
    """Schema for account update."""
    name: Optional[str] = None
    currency: Optional[str] = None
    balance: Optional[Decimal] = None
    description: Optional[str] = None


class AccountResponse(BaseModel):
    """Schema for account response."""
    id: int
    user_id: int
    name: str
    account_type: str
    currency: str
    balance: Decimal
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
