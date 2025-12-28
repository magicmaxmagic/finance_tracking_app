"""Category schemas for request/response validation."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class CategoryCreate(BaseModel):
    """Schema for category creation."""
    name: str = Field(..., max_length=255)
    color: str = "#000000"
    icon: Optional[str] = None
    is_income: bool = False
    description: Optional[str] = None


class CategoryUpdate(BaseModel):
    """Schema for category update."""
    name: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_income: Optional[bool] = None
    description: Optional[str] = None


class CategoryResponse(BaseModel):
    """Schema for category response."""
    id: int
    user_id: int
    name: str
    color: str
    icon: Optional[str]
    is_income: bool
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RuleTypeEnum(str):
    """Rule type enum."""
    CONTAINS = "contains"
    REGEX = "regex"
    EXACT_MATCH = "exact_match"


class CategoryRuleCreate(BaseModel):
    """Schema for category rule creation."""
    rule_type: str
    pattern: str = Field(..., max_length=500)
    priority: int = 0
    is_active: bool = True


class CategoryRuleResponse(BaseModel):
    """Schema for category rule response."""
    id: int
    category_id: int
    rule_type: str
    pattern: str
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
