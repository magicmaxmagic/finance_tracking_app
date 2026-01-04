"""Pure strategy engine for trajectory simulations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Iterable


@dataclass(frozen=True)
class StrategyAssumptions:
    income_growth_rate: Decimal
    expense_inflation_rate: Decimal
    investment_return_rate: Decimal
    volatility: Decimal


@dataclass(frozen=True)
class StrategyAction:
    action_type: str
    value: Decimal
    start_date: date
    end_date: date | None = None


@dataclass(frozen=True)
class TrajectoryPoint:
    month_index: int
    date: date
    net_worth: Decimal
    income: Decimal
    expenses: Decimal
    contribution: Decimal
    return_applied: Decimal


@dataclass(frozen=True)
class SensitivityResult:
    label: str
    net_worth: Decimal
    months_to_goal: int | None


@dataclass(frozen=True)
class TrajectoryResult:
    start_net_worth: Decimal
    target_value: Decimal | None
    time_to_goal_months: int | None
    capital_gap: Decimal | None
    trajectory: list[TrajectoryPoint]
    sensitivity: list[SensitivityResult]


ACTION_INCOME_DELTA = "income_delta"
ACTION_EXPENSE_DELTA = "expense_delta"
ACTION_INVESTMENT_DELTA = "investment_delta"
ACTION_ONE_TIME = "one_time_investment"


def _monthly_rate_from_annual(rate_pct: Decimal) -> Decimal:
    annual = float(rate_pct) / 100.0
    monthly = (1 + annual) ** (1 / 12) - 1
    return Decimal(str(monthly))


def _month_start(value: date) -> date:
    return date(value.year, value.month, 1)


def _add_months(value: date, months: int) -> date:
    year = value.year + (value.month - 1 + months) // 12
    month = (value.month - 1 + months) % 12 + 1
    return date(year, month, 1)


def _month_key(value: date) -> tuple[int, int]:
    return value.year, value.month


def _month_in_range(current: date, start: date, end: date | None) -> bool:
    current_key = _month_key(_month_start(current))
    start_key = _month_key(_month_start(start))
    end_key = _month_key(_month_start(end)) if end else None
    if current_key < start_key:
        return False
    if end_key and current_key > end_key:
        return False
    return True


def _apply_actions(actions: Iterable[StrategyAction], month_date: date) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    income_delta = Decimal("0")
    expense_delta = Decimal("0")
    investment_delta = Decimal("0")
    one_time = Decimal("0")

    for action in actions:
        if action.action_type == ACTION_ONE_TIME:
            if _month_key(month_date) == _month_key(action.start_date):
                one_time += action.value
            continue
        if not _month_in_range(month_date, action.start_date, action.end_date):
            continue
        if action.action_type == ACTION_INCOME_DELTA:
            income_delta += action.value
        elif action.action_type == ACTION_EXPENSE_DELTA:
            expense_delta += action.value
        elif action.action_type == ACTION_INVESTMENT_DELTA:
            investment_delta += action.value

    return income_delta, expense_delta, investment_delta, one_time


def _simulate(
    start_net_worth: Decimal,
    monthly_income: Decimal,
    monthly_expenses: Decimal,
    assumptions: StrategyAssumptions,
    actions: Iterable[StrategyAction],
    start_date: date,
    months: int,
    target_value: Decimal | None,
) -> tuple[list[TrajectoryPoint], int | None]:
    trajectory: list[TrajectoryPoint] = []
    income = Decimal(str(monthly_income))
    expenses = Decimal(str(monthly_expenses))
    net_worth = Decimal(str(start_net_worth))

    income_growth = _monthly_rate_from_annual(assumptions.income_growth_rate)
    expense_growth = _monthly_rate_from_annual(assumptions.expense_inflation_rate)
    return_rate = _monthly_rate_from_annual(assumptions.investment_return_rate)

    time_to_goal: int | None = None

    for idx in range(1, months + 1):
        month_date = _add_months(start_date, idx - 1)
        if idx > 1:
            income = income * (Decimal("1") + income_growth)
            expenses = expenses * (Decimal("1") + expense_growth)

        income_delta, expense_delta, investment_delta, one_time = _apply_actions(actions, month_date)
        month_income = income + income_delta
        month_expenses = expenses + expense_delta
        contribution = month_income - month_expenses + investment_delta

        net_worth_before = net_worth + contribution + one_time
        return_applied = net_worth_before * return_rate
        net_worth = net_worth_before + return_applied

        trajectory.append(
            TrajectoryPoint(
                month_index=idx,
                date=month_date,
                net_worth=net_worth,
                income=month_income,
                expenses=month_expenses,
                contribution=contribution,
                return_applied=return_applied,
            )
        )

        if target_value is not None and time_to_goal is None and net_worth >= target_value:
            time_to_goal = idx

    return trajectory, time_to_goal


def simulate_trajectory(
    start_net_worth: Decimal,
    monthly_income: Decimal,
    monthly_expenses: Decimal,
    assumptions: StrategyAssumptions,
    actions: Iterable[StrategyAction],
    start_date: date,
    months: int,
    target_value: Decimal | None = None,
) -> TrajectoryResult:
    """Run deterministic trajectory simulation."""
    trajectory, time_to_goal = _simulate(
        start_net_worth,
        monthly_income,
        monthly_expenses,
        assumptions,
        actions,
        start_date,
        months,
        target_value,
    )

    final_net_worth = trajectory[-1].net_worth if trajectory else start_net_worth
    capital_gap: Decimal | None = None
    if target_value is not None and time_to_goal is None:
        gap = target_value - final_net_worth
        capital_gap = gap if gap > 0 else Decimal("0")

    sensitivity: list[SensitivityResult] = []
    if assumptions.volatility > 0:
        optimistic = StrategyAssumptions(
            income_growth_rate=assumptions.income_growth_rate,
            expense_inflation_rate=assumptions.expense_inflation_rate,
            investment_return_rate=assumptions.investment_return_rate + assumptions.volatility,
            volatility=assumptions.volatility,
        )
        pessimistic = StrategyAssumptions(
            income_growth_rate=assumptions.income_growth_rate,
            expense_inflation_rate=assumptions.expense_inflation_rate,
            investment_return_rate=assumptions.investment_return_rate - assumptions.volatility,
            volatility=assumptions.volatility,
        )
        for label, assumption in ("optimistic", optimistic), ("pessimistic", pessimistic):
            alt_traj, alt_time = _simulate(
                start_net_worth,
                monthly_income,
                monthly_expenses,
                assumption,
                actions,
                start_date,
                months,
                target_value,
            )
            alt_final = alt_traj[-1].net_worth if alt_traj else start_net_worth
            sensitivity.append(
                SensitivityResult(label=label, net_worth=alt_final, months_to_goal=alt_time)
            )

    return TrajectoryResult(
        start_net_worth=start_net_worth,
        target_value=target_value,
        time_to_goal_months=time_to_goal,
        capital_gap=capital_gap,
        trajectory=trajectory,
        sensitivity=sensitivity,
    )
