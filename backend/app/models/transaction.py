"""Transaction model for financial transactions."""
from sqlalchemy import Column, String, Numeric, DateTime, Integer, ForeignKey, Text, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Transaction(Base):
    """Transaction model."""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    
    # Transaction details
    description = Column(String(500), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    transaction_date = Column(DateTime, nullable=False)
    
    # Metadata
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    notes = Column(Text, nullable=True)
    is_duplicate = Column(Boolean, default=False)
    duplicate_of_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    import_id = Column(String(255), nullable=True, unique=True)  # For CSV import deduplication
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_user_date', 'user_id', 'transaction_date'),
        Index('idx_account_date', 'account_id', 'transaction_date'),
        Index('idx_category_date', 'category_id', 'transaction_date'),
        Index('idx_import_id', 'import_id'),
    )
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
