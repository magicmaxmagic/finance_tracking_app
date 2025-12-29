"""FX rate model for multi-currency support."""
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Integer, Numeric, Date, Index
from app.db.base import Base


class FXRate(Base):
    """Foreign exchange rate model."""
    __tablename__ = "fx_rates"

    id = Column(Integer, primary_key=True, index=True)
    base_currency = Column(String(3), nullable=False)
    quote_currency = Column(String(3), nullable=False)
    rate = Column(Numeric(18, 8), nullable=False)
    as_of = Column(Date, default=date.today, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_fx_pair_date", "base_currency", "quote_currency", "as_of", unique=True),
    )
