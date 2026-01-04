"""Schedule schemas for request/response validation."""
from datetime import datetime, time
from pydantic import BaseModel, Field


class ScheduleBlockBase(BaseModel):
    """Base schema for schedule blocks."""

    title: str = Field(..., max_length=255)
    description: str | None = Field(None, max_length=500)
    category: str = Field(..., max_length=32)
    day_of_week: int = Field(..., ge=0, le=6)
    start_time: time
    duration_minutes: int = Field(..., ge=1, le=1440)
    is_active: bool = True


class ScheduleBlockCreate(ScheduleBlockBase):
    """Schema for schedule block creation."""


class ScheduleBlockUpdate(BaseModel):
    """Schema for schedule block update."""

    title: str | None = Field(None, max_length=255)
    description: str | None = Field(None, max_length=500)
    category: str | None = Field(None, max_length=32)
    day_of_week: int | None = Field(None, ge=0, le=6)
    start_time: time | None = None
    duration_minutes: int | None = Field(None, ge=1, le=1440)
    is_active: bool | None = None


class ScheduleBlockResponse(ScheduleBlockBase):
    """Schema for schedule block response."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
