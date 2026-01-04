"""Tests for the strategy engine."""
from datetime import date
from decimal import Decimal

from app.services.strategy_engine import (
    StrategyAssumptions,
    StrategyAction,
    simulate_trajectory,
    ACTION_ONE_TIME,
    ACTION_EXPENSE_DELTA,
)


def test_trajectory_without_returns():
    assumptions = StrategyAssumptions(
        income_growth_rate=Decimal("0"),
        expense_inflation_rate=Decimal("0"),
        investment_return_rate=Decimal("0"),
        volatility=Decimal("0"),
    )
    result = simulate_trajectory(
        start_net_worth=Decimal("10000"),
        monthly_income=Decimal("3000"),
        monthly_expenses=Decimal("2000"),
        assumptions=assumptions,
        actions=[],
        start_date=date(2025, 1, 1),
        months=12,
        target_value=Decimal("15000"),
    )
    assert result.trajectory[-1].net_worth == Decimal("22000")
    assert result.time_to_goal_months == 5


def test_trajectory_with_one_time_action():
    assumptions = StrategyAssumptions(
        income_growth_rate=Decimal("0"),
        expense_inflation_rate=Decimal("0"),
        investment_return_rate=Decimal("0"),
        volatility=Decimal("0"),
    )
    actions = [
        StrategyAction(
            action_type=ACTION_ONE_TIME,
            value=Decimal("5000"),
            start_date=date(2025, 1, 1),
            end_date=None,
        )
    ]
    result = simulate_trajectory(
        start_net_worth=Decimal("10000"),
        monthly_income=Decimal("3000"),
        monthly_expenses=Decimal("2000"),
        assumptions=assumptions,
        actions=actions,
        start_date=date(2025, 1, 1),
        months=3,
        target_value=Decimal("15000"),
    )
    assert result.time_to_goal_months == 1


def test_expense_reduction_action():
    assumptions = StrategyAssumptions(
        income_growth_rate=Decimal("0"),
        expense_inflation_rate=Decimal("0"),
        investment_return_rate=Decimal("0"),
        volatility=Decimal("0"),
    )
    actions = [
        StrategyAction(
            action_type=ACTION_EXPENSE_DELTA,
            value=Decimal("-200"),
            start_date=date(2025, 1, 1),
            end_date=None,
        )
    ]
    result = simulate_trajectory(
        start_net_worth=Decimal("10000"),
        monthly_income=Decimal("3000"),
        monthly_expenses=Decimal("2000"),
        assumptions=assumptions,
        actions=actions,
        start_date=date(2025, 1, 1),
        months=1,
        target_value=None,
    )
    assert result.trajectory[0].net_worth == Decimal("11200")
