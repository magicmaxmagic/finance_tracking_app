"""Net worth snapshot model for tracking net worth over time."""
from sqlalchemy import Column, Numeric, DateTime, Integer, ForeignKey, Date, Index
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.db.base import Base


class NetWorthSnapshot(Base):
    """Monthly net worth snapshot model."""
    __tablename__ = "net_worth_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    
    # Snapshot details
    snapshot_date = Column(Date, nullable=False)  # Date of snapshot
    balance = Column(Numeric(15, 2), nullable=False)  # Account balance at that date
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_user_date', 'user_id', 'snapshot_date'),
        Index('idx_account_date', 'account_id', 'snapshot_date'),
    )
    
    # Relationships
    user = relationship("User", back_populates="net_worth_snapshots")
    account = relationship("Account", back_populates="net_worth_entries")
