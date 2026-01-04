"""Schemas for external calendar integrations."""
from datetime import datetime, date
from enum import Enum
from pydantic import BaseModel, EmailStr, Field


class CalendarProvider(str, Enum):
    APPLE = "apple"
    GOOGLE = "google"


class AppleCalendarConnectRequest(BaseModel):
    email: EmailStr
    app_password: str = Field(..., min_length=8)
    calendar_name: str | None = None


class CalendarInfoResponse(BaseModel):
    name: str
    url: str


class CalendarConnectionResponse(BaseModel):
    id: int
    provider: CalendarProvider
    account_email: EmailStr
    calendar_name: str | None = None
    is_active: bool
    last_sync_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CalendarEventResponse(BaseModel):
    start: datetime | date
    end: datetime | date
    summary: str | None = None
    is_all_day: bool = False


class CalendarImportStatus(BaseModel):
    provider: CalendarProvider
    source: str
    calendar_name: str | None = None
    event_count: int
    last_imported_at: datetime | None = None
