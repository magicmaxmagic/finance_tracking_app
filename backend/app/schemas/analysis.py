"""Analysis schemas for forecasting."""
from pydantic import BaseModel, Field
from decimal import Decimal
from typing import List


class ForecastRequest(BaseModel):
    """Schema for forecast request."""
    years: int = Field(5, ge=1, le=50)
    monthly_contribution: Decimal | None = None
    annual_return_rate: float = Field(5.0, ge=-50, le=50)


class ForecastPoint(BaseModel):
    """Schema for a forecast point."""
    year: int
    net_worth: Decimal


class ForecastResponse(BaseModel):
    """Schema for forecast response."""
    start_net_worth: Decimal
    monthly_contribution: Decimal
    annual_return_rate: float
    average_monthly_net: Decimal
    projection: List[ForecastPoint]
