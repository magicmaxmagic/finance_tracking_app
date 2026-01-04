"""Subscription model for plan management."""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Boolean, Enum as SQLEnum, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base


class SubscriptionPlan(str, Enum):
    """Subscription plan tiers."""
    STARTER = "starter"
    PRO = "pro"


class SubscriptionStatus(str, Enum):
    """Stripe subscription status values."""
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAUSED = "paused"


class UserSubscription(Base):
    """User subscription state and Stripe metadata."""

    __tablename__ = "user_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan = Column(
        SQLEnum(SubscriptionPlan, name="subscriptionplan", values_callable=lambda enum: [item.value for item in enum]),
        nullable=False,
        default=SubscriptionPlan.STARTER,
    )
    status = Column(
        SQLEnum(SubscriptionStatus, name="subscriptionstatus", values_callable=lambda enum: [item.value for item in enum]),
        nullable=True,
    )
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    stripe_price_id = Column(String(255), nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="subscription")

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_subscriptions_user"),
        Index("idx_user_subscriptions_user", "user_id"),
        Index("idx_user_subscriptions_customer", "stripe_customer_id"),
        Index("idx_user_subscriptions_subscription", "stripe_subscription_id"),
    )
