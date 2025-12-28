"""Net worth snapshot schemas for request/response validation."""
from pydantic import BaseModel
from datetime import datetime, date
from decimal import Decimal


class NetWorthSnapshotCreate(BaseModel):
    """Schema for net worth snapshot creation."""
    account_id: int
    snapshot_date: date
    balance: Decimal


class NetWorthSnapshotResponse(BaseModel):
    """Schema for net worth snapshot response."""
    id: int
    user_id: int
    account_id: int
    snapshot_date: date
    balance: Decimal
    created_at: datetime
    
    class Config:
        from_attributes = True


class NetWorthSummary(BaseModel):
    """Schema for net worth summary."""
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
    breakdown: dict[str, Decimal]  # By account type
    date: date
