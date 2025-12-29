"""Dashboard schemas for KPIs and analytics."""
from pydantic import BaseModel
from decimal import Decimal
from typing import List, Dict


class DashboardKPI(BaseModel):
    """Schema for dashboard KPI."""
    monthly_expenses: Decimal
    burn_rate: Decimal
    current_net_worth: Decimal


class CategoryExpense(BaseModel):
    """Schema for category expenses."""
    category_id: int
    category_name: str
    amount: Decimal
    percentage: float


class MonthlyExpense(BaseModel):
    """Schema for monthly expenses."""
    month: str
    total: Decimal


class DashboardData(BaseModel):
    """Schema for complete dashboard data."""
    kpi: DashboardKPI
    expenses_by_category: List[CategoryExpense]
    monthly_expenses: List[MonthlyExpense]
    recent_transactions: List[Dict]
    onboarding: List[Dict]
