"""Dashboard schemas for KPIs and analytics."""
from pydantic import BaseModel
from decimal import Decimal
from typing import List, Dict


class DashboardKPI(BaseModel):
    """Schema for dashboard KPI."""
    monthly_income: Decimal
    monthly_expenses: Decimal
    monthly_net: Decimal
    savings_rate: float
    burn_rate: Decimal
    current_net_worth: Decimal
    avg_monthly_income: Decimal
    avg_monthly_expenses: Decimal
    income_change_pct: float
    expense_change_pct: float
    net_change_pct: float
    time_to_goal_months: int | None = None
    required_savings_rate: float | None = None
    required_investment_rate: float | None = None
    trajectory_deviation_score: float | None = None
    decision_impact_score: float | None = None


class CategoryExpense(BaseModel):
    """Schema for category expenses."""
    category_id: int
    category_name: str
    amount: Decimal
    percentage: float


class AssetCategory(BaseModel):
    """Schema for asset allocation by category."""
    key: str
    label: str
    amount: Decimal
    percentage: float


class LabelExpense(BaseModel):
    """Schema for label breakdown."""
    label: str
    amount: Decimal
    percentage: float


class MonthlyExpense(BaseModel):
    """Schema for monthly expenses."""
    month: str
    total: Decimal


class MonthlyCashflow(BaseModel):
    """Schema for monthly cashflow."""
    month: str
    income: Decimal
    expenses: Decimal
    net: Decimal


class TopMerchant(BaseModel):
    """Schema for top merchant/source breakdown."""
    name: str
    amount: Decimal
    count: int


class DashboardData(BaseModel):
    """Schema for complete dashboard data."""
    kpi: DashboardKPI
    expenses_by_category: List[CategoryExpense]
    assets_by_category: List[AssetCategory]
    monthly_expenses: List[MonthlyExpense]
    cashflow: List[MonthlyCashflow]
    recent_transactions: List[Dict]
    onboarding: List[Dict]
    expenses_by_label: List[LabelExpense]
    income_by_label: List[LabelExpense]
    top_expense_merchants: List[TopMerchant]
    top_income_merchants: List[TopMerchant]
