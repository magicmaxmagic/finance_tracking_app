"""Schemas for user settings."""
from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class PlanEnum(str, Enum):
    STARTER = "starter"
    PRO = "pro"


class SubscriptionStatusEnum(str, Enum):
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAUSED = "paused"


class SettingsBase(BaseModel):
    currency: str
    timezone: str
    date_format: str
    start_of_week: str
    default_view: str
    data_retention: str
    digest_enabled: bool
    transaction_alerts: bool
    budget_alerts: bool
    auto_categorization: bool
    import_deduplication: bool
    analytics_opt_in: bool
    planning_preferences: dict | None = None


class SettingsUpdate(BaseModel):
    currency: str | None = None
    timezone: str | None = None
    date_format: str | None = None
    start_of_week: str | None = None
    default_view: str | None = None
    data_retention: str | None = None
    digest_enabled: bool | None = None
    transaction_alerts: bool | None = None
    budget_alerts: bool | None = None
    auto_categorization: bool | None = None
    import_deduplication: bool | None = None
    analytics_opt_in: bool | None = None
    planning_preferences: dict | None = None


class SettingsResponse(SettingsBase):
    id: int
    user_id: int
    calendar_feed_token: str | None = None
    plan: PlanEnum = PlanEnum.STARTER
    subscription_status: SubscriptionStatusEnum | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
