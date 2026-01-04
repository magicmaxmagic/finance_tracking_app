"""Schemas for investment assets."""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field


class InvestmentCategoryEnum(str, Enum):
    RENTAL = "rental"
    STOCKS = "stocks"
    FUNDS = "funds"
    CRYPTO = "crypto"
    PORTFOLIO = "portfolio"
    BUSINESS = "business"
    OTHER = "other"


class InvestmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category: InvestmentCategoryEnum
    current_value: Decimal = Field(..., ge=0)
    currency: str = Field("USD", min_length=3, max_length=3)
    notes: str | None = Field(None, max_length=500)
    is_active: bool = True


class InvestmentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    category: InvestmentCategoryEnum | None = None
    current_value: Decimal | None = Field(None, ge=0)
    currency: str | None = Field(None, min_length=3, max_length=3)
    notes: str | None = Field(None, max_length=500)
    is_active: bool | None = None


class InvestmentResponse(BaseModel):
    id: int
    user_id: int
    name: str
    category: InvestmentCategoryEnum
    current_value: Decimal
    currency: str
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
