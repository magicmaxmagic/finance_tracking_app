"""External calendar event model for imports."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.base import Base


class ExternalCalendarEvent(Base):
    """Imported calendar event (read-only)."""

    __tablename__ = "external_calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(32), nullable=False)
    source = Column(String(16), nullable=False, default="ics")
    calendar_name = Column(String(255), nullable=True)
    timezone = Column(String(64), nullable=True)
    summary = Column(String(255), nullable=True)
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=False)
    is_all_day = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="external_calendar_events")

    __table_args__ = (
        Index("idx_external_events_user", "user_id"),
        Index("idx_external_events_provider", "provider"),
        Index("idx_external_events_source", "source"),
        Index("idx_external_events_start", "starts_at"),
    )
