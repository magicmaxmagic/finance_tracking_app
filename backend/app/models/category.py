"""Category and rule models for transaction categorization."""
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.db.base import Base


class RuleType(str, Enum):
    """Types of categorization rules."""
    CONTAINS = "contains"
    REGEX = "regex"
    EXACT_MATCH = "exact_match"


class Category(Base):
    """Transaction category model."""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    color = Column(String(7), default="#000000", nullable=False)  # Hex color
    icon = Column(String(50), nullable=True)  # Icon name/emoji
    is_income = Column(Boolean, default=False)  # True for income categories, False for expenses
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category", cascade="all, delete-orphan")
    rules = relationship("CategoryRule", back_populates="category", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="category", cascade="all, delete-orphan")


class CategoryRule(Base):
    """Rules for automatic categorization."""
    __tablename__ = "category_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    rule_type = Column(SQLEnum(RuleType), nullable=False)
    pattern = Column(String(500), nullable=False)  # Contains string, regex pattern, or exact match
    priority = Column(Integer, default=0)  # Higher priority rules are applied first
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = relationship("Category", back_populates="rules")
