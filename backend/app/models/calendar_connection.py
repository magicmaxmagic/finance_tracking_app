"""Calendar connection model for external providers."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base


class CalendarConnection(Base):
    """External calendar connection (read-only)."""

    __tablename__ = "calendar_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(32), nullable=False)
    account_email = Column(String(255), nullable=False)
    calendar_name = Column(String(255), nullable=True)
    calendar_url = Column(String(512), nullable=True)
    encrypted_secret = Column(String(1024), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="calendar_connections")

    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_calendar_connections_user_provider"),
        Index("idx_calendar_connections_user", "user_id"),
        Index("idx_calendar_connections_provider", "provider"),
    )
