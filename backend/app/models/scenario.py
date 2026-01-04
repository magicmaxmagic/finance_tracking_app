"""Scenario model for strategy simulations."""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Numeric, Date, DateTime, Integer, ForeignKey, Boolean, Enum as SQLEnum, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base


class ActionType(str, Enum):
    """Action types for scenario adjustments."""
    INCOME_DELTA = "income_delta"
    EXPENSE_DELTA = "expense_delta"
    INVESTMENT_DELTA = "investment_delta"
    ONE_TIME_INVESTMENT = "one_time_investment"


class Scenario(Base):
    """Scenario for financial strategy modeling."""
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    goal_id = Column(Integer, ForeignKey("financial_goals.id", ondelete="SET NULL"), nullable=True)
    assumption_id = Column(Integer, ForeignKey("assumption_versions.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    scenario_group_id = Column(String(36), nullable=False)
    version = Column(Integer, nullable=False)
    is_baseline = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    goal = relationship("FinancialGoal", back_populates="scenarios")
    assumption_version = relationship("AssumptionVersion", back_populates="scenarios")
    actions = relationship("ScenarioAction", back_populates="scenario", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("scenario_group_id", "version", name="uq_scenario_group_version"),
        Index("idx_scenario_user_active", "user_id", "is_active"),
    )


class ScenarioAction(Base):
    """Action applied within a scenario."""
    __tablename__ = "scenario_actions"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False)
    action_type = Column(
        SQLEnum(ActionType, name="actiontype", values_callable=lambda enum: [item.value for item in enum]),
        nullable=False,
    )
    value = Column(Numeric(15, 2), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    scenario = relationship("Scenario", back_populates="actions")

    __table_args__ = (
        Index("idx_action_scenario", "scenario_id"),
    )
