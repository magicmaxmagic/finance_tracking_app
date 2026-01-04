"""Onboarding profile model."""
from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column,
    String,
    Numeric,
    Date,
    DateTime,
    Integer,
    ForeignKey,
    Boolean,
    Enum as SQLEnum,
    JSON,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from app.db.base import Base


class RiskAppetite(str, Enum):
    """Risk appetite levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class InvestorProfile(str, Enum):
    """Investor profile types."""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    GROWTH = "growth"
    ACTIVE = "active"


class OnboardingProfile(Base):
    """Onboarding profile collected during first run."""

    __tablename__ = "onboarding_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    risk_appetite = Column(
        SQLEnum(
            RiskAppetite,
            name="riskappetite",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )
    investor_profile = Column(
        SQLEnum(
            InvestorProfile,
            name="investorprofile",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )
    goal_value = Column(Numeric(18, 2), nullable=False)
    goal_horizon_years = Column(Integer, nullable=False)
    target_date = Column(Date, nullable=False)
    asset_allocation = Column(JSON, nullable=False, default=list)
    investment_interests = Column(JSON, nullable=False, default=list)
    vision = Column(String(500), nullable=True)
    is_completed = Column(Boolean, default=True)
    completed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="onboarding_profile")

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_onboarding_user"),
        Index("idx_onboarding_user", "user_id"),
    )
