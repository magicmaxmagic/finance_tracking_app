"""Schedule block model for weekly planning."""
from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, String, Time, Boolean, DateTime, Index
from sqlalchemy.orm import relationship
from app.db.base import Base


class ScheduleBlock(Base):
    """Weekly schedule block."""

    __tablename__ = "schedule_blocks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    category = Column(String(32), nullable=False, default="FINANCE")
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=60)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="schedule_blocks")

    __table_args__ = (
        Index("idx_schedule_blocks_user", "user_id"),
        Index("idx_schedule_blocks_user_day", "user_id", "day_of_week"),
    )
