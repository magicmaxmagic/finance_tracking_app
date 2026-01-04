"""User settings model."""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base


class UserSettings(Base):
    """User settings for preferences and automation."""

    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    timezone = Column(String(64), nullable=False, default="America/New_York")
    date_format = Column(String(24), nullable=False, default="MM/DD/YYYY")
    start_of_week = Column(String(16), nullable=False, default="Monday")
    default_view = Column(String(32), nullable=False, default="dashboard")
    data_retention = Column(String(32), nullable=False, default="forever")
    digest_enabled = Column(Boolean, nullable=False, default=True)
    transaction_alerts = Column(Boolean, nullable=False, default=True)
    budget_alerts = Column(Boolean, nullable=False, default=True)
    auto_categorization = Column(Boolean, nullable=False, default=True)
    import_deduplication = Column(Boolean, nullable=False, default=True)
    analytics_opt_in = Column(Boolean, nullable=False, default=True)
    calendar_feed_token = Column(String(128), nullable=True)
    planning_preferences = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="settings")

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_settings_user"),
        Index("idx_user_settings_user", "user_id"),
        Index("idx_user_settings_calendar_feed_token", "calendar_feed_token", unique=True),
    )
