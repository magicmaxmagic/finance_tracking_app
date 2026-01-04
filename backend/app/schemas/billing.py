"""Schemas for billing and subscriptions."""
from enum import Enum
from pydantic import BaseModel


class BillingInterval(str, Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"


class CheckoutRequest(BaseModel):
    interval: BillingInterval = BillingInterval.MONTHLY


class CheckoutResponse(BaseModel):
    url: str


class PortalResponse(BaseModel):
    url: str
