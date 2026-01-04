"""Investment asset model for third-party holdings."""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Numeric, DateTime, Boolean, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.base import Base


class InvestmentCategory(str, Enum):
    """Supported investment categories."""
    RENTAL = "rental"
    STOCKS = "stocks"
    FUNDS = "funds"
    CRYPTO = "crypto"
    PORTFOLIO = "portfolio"
    BUSINESS = "business"
    OTHER = "other"


class InvestmentAsset(Base):
    """Third-party investment asset."""

    __tablename__ = "investment_assets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(
        SQLEnum(
            InvestmentCategory,
            name="investmentcategory",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )
    current_value = Column(Numeric(18, 2), nullable=False, default=0)
    currency = Column(String(3), default="USD", nullable=False)
    notes = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="investment_assets")
