"""Financial goal model."""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Numeric, Date, DateTime, Integer, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from app.db.base import Base


class GoalType(str, Enum):
    """Supported financial goal types."""
    NET_WORTH = "net_worth"
    LIQUID_ASSETS = "liquid_assets"


class GoalStatus(str, Enum):
    """Goal lifecycle status."""
    ACTIVE = "active"
    ACHIEVED = "achieved"
    ARCHIVED = "archived"


class FinancialGoal(Base):
    """Financial goal for strategy planning."""
    __tablename__ = "financial_goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    target_type = Column(
        SQLEnum(GoalType, name="goaltype", values_callable=lambda enum: [item.value for item in enum]),
        nullable=False,
    )
    target_value = Column(Numeric(18, 2), nullable=False)
    target_date = Column(Date, nullable=False)
    status = Column(
        SQLEnum(GoalStatus, name="goalstatus", values_callable=lambda enum: [item.value for item in enum]),
        nullable=False,
        default=GoalStatus.ACTIVE,
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="financial_goals")
    scenarios = relationship("Scenario", back_populates="goal", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_goal_user_status", "user_id", "status"),
        Index("idx_goal_user_target", "user_id", "target_date"),
    )
