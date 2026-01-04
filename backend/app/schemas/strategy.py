"""Schemas for strategy engine responses."""
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from app.schemas.scenario import ScenarioActionCreate


class TrajectoryRequest(BaseModel):
    """Request payload for trajectory simulation."""
    goal_id: Optional[int] = None
    assumption_id: Optional[int] = None
    scenario_id: Optional[int] = None
    months: Optional[int] = Field(None, ge=1, le=600)
    actions: List[ScenarioActionCreate] = []


class TrajectoryPoint(BaseModel):
    """Monthly trajectory output."""
    month_index: int
    date: date
    net_worth: Decimal
    income: Decimal
    expenses: Decimal
    contribution: Decimal
    return_applied: Decimal


class SensitivityResult(BaseModel):
    """Sensitivity analysis result."""
    label: str
    net_worth: Decimal
    months_to_goal: Optional[int]


class TrajectoryResponse(BaseModel):
    """Trajectory response."""
    start_net_worth: Decimal
    target_value: Optional[Decimal]
    target_date: Optional[date]
    time_to_goal_months: Optional[int]
    capital_gap: Optional[Decimal]
    sensitivity: List[SensitivityResult]
    trajectory: List[TrajectoryPoint]


class ScenarioCompareRequest(BaseModel):
    """Compare scenarios request."""
    scenario_ids: List[int]


class ScenarioComparisonItem(BaseModel):
    scenario_id: int
    name: str
    months_to_goal: Optional[int]
    final_net_worth: Decimal
    delta_months: Optional[int]
    delta_net_worth: Decimal


class ScenarioComparisonResponse(BaseModel):
    baseline_scenario_id: int
    comparisons: List[ScenarioComparisonItem]


class DecisionImpact(BaseModel):
    name: str
    action_type: str
    monthly_delta: Decimal
    months_saved: Optional[int]
    efficiency_score: Optional[float]


class DecisionRecommendation(BaseModel):
    headline: str
    detail: str


class DecisionOverview(BaseModel):
    decision_impact_score: Optional[float]
    opportunities: List[DecisionImpact]
    recommendations: List[DecisionRecommendation]


class StrategyAlert(BaseModel):
    deviation_score: Optional[float]
    expected_net_worth: Optional[Decimal]
    actual_net_worth: Optional[Decimal]
    message: Optional[str]
