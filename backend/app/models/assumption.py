"""Assumption version model for strategy simulation."""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Numeric, DateTime, Integer, ForeignKey, Boolean, Enum as SQLEnum, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base


class RiskLevel(str, Enum):
    """Risk tolerance levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AssumptionVersion(Base):
    """Immutable assumption version."""
    __tablename__ = "assumption_versions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    version = Column(Integer, nullable=False)
    income_growth_rate = Column(Numeric(6, 3), nullable=False, default=0)
    expense_inflation_rate = Column(Numeric(6, 3), nullable=False, default=0)
    investment_return_rate = Column(Numeric(6, 3), nullable=False, default=0)
    volatility = Column(Numeric(6, 3), nullable=False, default=0)
    risk_level = Column(
        SQLEnum(RiskLevel, name="risklevel", values_callable=lambda enum: [item.value for item in enum]),
        nullable=False,
        default=RiskLevel.MEDIUM,
    )
    notes = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="assumption_versions")
    scenarios = relationship("Scenario", back_populates="assumption_version")

    __table_args__ = (
        UniqueConstraint("user_id", "version", name="uq_assumption_version_user"),
        Index("idx_assumption_user_active", "user_id", "is_active"),
    )
