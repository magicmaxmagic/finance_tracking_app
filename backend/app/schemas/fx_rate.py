"""FX rate schemas."""
from pydantic import BaseModel
from datetime import date, datetime


class FXRateUpsert(BaseModel):
    base_currency: str
    quote_currency: str
    rate: float
    as_of: date


class FXRateResponse(BaseModel):
    id: int
    base_currency: str
    quote_currency: str
    rate: float
    as_of: date
    created_at: datetime

    class Config:
        from_attributes = True
