"""Transaction schemas for request/response validation."""
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional
from decimal import Decimal


class TransactionCreate(BaseModel):
    """Schema for transaction creation."""
    account_id: int
    description: str = Field(..., max_length=500)
    amount: Decimal
    currency: str = "USD"
    transaction_date: datetime
    category_id: Optional[int] = None
    tags: Optional[str] = None
    notes: Optional[str] = None


class TransactionUpdate(BaseModel):
    """Schema for transaction update."""
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    transaction_date: Optional[datetime] = None
    category_id: Optional[int] = None
    tags: Optional[str] = None
    notes: Optional[str] = None


class TransactionResponse(BaseModel):
    """Schema for transaction response."""
    id: int
    user_id: int
    account_id: int
    category_id: Optional[int]
    description: str
    amount: Decimal
    currency: str
    transaction_date: datetime
    tags: Optional[str]
    notes: Optional[str]
    is_duplicate: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """Schema for transaction list response."""
    items: list[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CSVImportRequest(BaseModel):
    """Schema for CSV import request."""
    account_id: int
    column_mapping: dict[str, str]  # e.g., {"Date": "transaction_date", "Amount": "amount"}
    skip_duplicates: bool = True
