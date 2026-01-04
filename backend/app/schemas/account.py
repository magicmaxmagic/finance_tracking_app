"""Account schemas for request/response validation."""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from decimal import Decimal
from enum import Enum


class AccountTypeEnum(str, Enum):
    """Account type enum."""
    CASH = "cash"
    SAVINGS = "savings"
    CHECKING = "checking"
    CREDIT = "credit"
    INVESTMENT = "investment"
    DEBT = "debt"
    OTHER = "other"

    @classmethod
    def normalize(cls, value: str) -> str:
        """Normalize user input to a supported account type."""
        cleaned = value.strip().lower()
        synonyms = {
            "chequing": "checking",
            "current": "checking",
            "current account": "checking",
            "cc": "credit",
            "credit card": "credit",
        }
        return synonyms.get(cleaned, cleaned)


class AccountCreate(BaseModel):
    """Schema for account creation."""
    name: str = Field(..., max_length=255)
    account_type: AccountTypeEnum
    currency: str = "USD"
    balance: Decimal = Decimal("0.00")
    description: Optional[str] = None

    @field_validator("account_type", mode="before")
    @classmethod
    def normalize_account_type(cls, value):
        if isinstance(value, AccountTypeEnum):
            return value
        if not isinstance(value, str):
            raise ValueError("account_type must be a string")
        return AccountTypeEnum.normalize(value)


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
