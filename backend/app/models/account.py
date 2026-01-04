"""Account model for financial accounts."""
from sqlalchemy import Column, String, Numeric, DateTime, Boolean, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.db.base import Base


class AccountType(str, Enum):
    """Account types."""
    CASH = "cash"
    SAVINGS = "savings"
    CHECKING = "checking"
    CREDIT = "credit"
    INVESTMENT = "investment"
    DEBT = "debt"
    OTHER = "other"


class Account(Base):
    """Account model."""
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    account_type = Column(
        SQLEnum(
            AccountType,
            name="accounttype",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )
    currency = Column(String(3), default="USD", nullable=False)
    balance = Column(Numeric(15, 2), default=0, nullable=False)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    net_worth_entries = relationship("NetWorthSnapshot", back_populates="account")
