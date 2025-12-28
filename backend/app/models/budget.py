"""Budget model for monthly budget tracking."""
from sqlalchemy import Column, Numeric, DateTime, Integer, ForeignKey, Date, Index
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.db.base import Base


class Budget(Base):
    """Monthly budget model."""
    __tablename__ = "budgets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    
    # Budget details
    amount = Column(Numeric(15, 2), nullable=False)  # Monthly limit
    month = Column(Date, nullable=False)  # First day of the month
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_user_month', 'user_id', 'month'),
        Index('idx_category_month', 'category_id', 'month'),
    )
    
    # Relationships
    user = relationship("User", back_populates="budgets")
    category = relationship("Category", back_populates="budgets")
