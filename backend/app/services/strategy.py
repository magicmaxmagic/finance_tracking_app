"""Strategy service for decision-oriented financial planning."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_CEILING
from typing import Iterable

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import AccountType
from app.models.financial_goal import GoalType
from app.models.transaction import Transaction
from app.repositories.assumption import AssumptionRepository
from app.repositories.financial_goal import FinancialGoalRepository
from app.repositories.scenario import ScenarioRepository
from app.schemas.strategy import (
    DecisionImpact,
    DecisionOverview,
    DecisionRecommendation,
    ScenarioComparisonResponse,
    ScenarioComparisonItem,
    StrategyAlert,
    TrajectoryRequest,
    TrajectoryResponse,
    TrajectoryPoint as TrajectoryPointSchema,
    SensitivityResult as SensitivityResultSchema,
)
from app.services.net_worth import NetWorthService
from app.services.strategy_engine import (
    StrategyAssumptions,
    StrategyAction,
    simulate_trajectory,
    ACTION_EXPENSE_DELTA,
    ACTION_INCOME_DELTA,
    ACTION_INVESTMENT_DELTA,
)


@dataclass(frozen=True)
class CashflowBaseline:
    avg_income: Decimal
    avg_expenses: Decimal
    current_income: Decimal
    current_expenses: Decimal


class StrategyService:
    """Service for trajectory simulations and decision intelligence."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.net_worth_service = NetWorthService(session)
        self.goal_repository = FinancialGoalRepository(session)
        self.assumption_repository = AssumptionRepository(session)
        self.scenario_repository = ScenarioRepository(session)

    async def run_trajectory(self, user_id: int, request: TrajectoryRequest) -> TrajectoryResponse:
        scenario = None
        if request.scenario_id:
            scenario = await self.scenario_repository.get_by_id(request.scenario_id, user_id)
            if not scenario:
                raise ValueError("Scenario not found")

        goal_id = request.goal_id or (scenario.goal_id if scenario else None)
        assumption_id = request.assumption_id or (scenario.assumption_id if scenario else None)

        goal = await self._resolve_goal(user_id, goal_id)
        assumptions = await self._resolve_assumptions(user_id, assumption_id)
        baseline = await self._get_cashflow_baseline(user_id)
        start_date = date.today().replace(day=1)
        start_net_worth = await self._get_starting_net_worth(user_id, goal)

        actions = self._build_actions(scenario.actions if scenario else [], request.actions)

        months = request.months or self._months_from_goal(start_date, goal)
        result = simulate_trajectory(
            start_net_worth=start_net_worth,
            monthly_income=baseline.avg_income,
            monthly_expenses=baseline.avg_expenses,
            assumptions=assumptions,
            actions=actions,
            start_date=start_date,
            months=months,
            target_value=goal.target_value if goal else None,
        )

        trajectory = [
            TrajectoryPointSchema(
                month_index=point.month_index,
                date=point.date,
                net_worth=point.net_worth,
                income=point.income,
                expenses=point.expenses,
                contribution=point.contribution,
                return_applied=point.return_applied,
            )
            for point in result.trajectory
        ]

        sensitivity = [
            SensitivityResultSchema(
                label=item.label,
                net_worth=item.net_worth,
                months_to_goal=item.months_to_goal,
            )
            for item in result.sensitivity
        ]

        return TrajectoryResponse(
            start_net_worth=result.start_net_worth,
            target_value=goal.target_value if goal else None,
            target_date=goal.target_date if goal else None,
            time_to_goal_months=result.time_to_goal_months,
            capital_gap=result.capital_gap,
            sensitivity=sensitivity,
            trajectory=trajectory,
        )

    async def compare_scenarios(self, user_id: int, scenario_ids: list[int]) -> ScenarioComparisonResponse:
        scenarios = []
        for scenario_id in scenario_ids:
            scenario = await self.scenario_repository.get_by_id(scenario_id, user_id)
            if not scenario:
                raise ValueError(f"Scenario {scenario_id} not found")
            scenarios.append(scenario)

        baseline = next((scenario for scenario in scenarios if scenario.is_baseline), scenarios[0])
        baseline_goal_id = baseline.goal_id

        baseline_result = await self.run_trajectory(
            user_id,
            TrajectoryRequest(scenario_id=baseline.id, goal_id=baseline_goal_id),
        )
        baseline_months = baseline_result.time_to_goal_months
        baseline_final = baseline_result.trajectory[-1].net_worth if baseline_result.trajectory else baseline_result.start_net_worth

        comparisons = []
        for scenario in scenarios:
            result = await self.run_trajectory(
                user_id,
                TrajectoryRequest(scenario_id=scenario.id, goal_id=baseline_goal_id),
            )
            final_net_worth = result.trajectory[-1].net_worth if result.trajectory else result.start_net_worth
            months_to_goal = result.time_to_goal_months
            delta_months = None
            if baseline_months is not None and months_to_goal is not None:
                delta_months = baseline_months - months_to_goal
            comparisons.append(
                ScenarioComparisonItem(
                    scenario_id=scenario.id,
                    name=scenario.name,
                    months_to_goal=months_to_goal,
                    final_net_worth=final_net_worth,
                    delta_months=delta_months,
                    delta_net_worth=final_net_worth - baseline_final,
                )
            )

        return ScenarioComparisonResponse(
            baseline_scenario_id=baseline.id,
            comparisons=comparisons,
        )

    async def get_decision_overview(
        self, user_id: int, goal_id: int | None = None, assumption_id: int | None = None
    ) -> DecisionOverview:
        goal = await self._resolve_goal(user_id, goal_id)
        if not goal:
            return DecisionOverview(
                decision_impact_score=0,
                opportunities=[],
                recommendations=[
                    DecisionRecommendation(
                        headline="Set a goal to unlock decision insights",
                        detail="Create a financial goal to measure the impact of new actions.",
                    )
                ],
            )

        baseline_result = await self.run_trajectory(
            user_id,
            TrajectoryRequest(goal_id=goal_id, assumption_id=assumption_id),
        )
        baseline_months = baseline_result.time_to_goal_months
        if baseline_months is None:
            baseline = await self._get_cashflow_baseline(user_id)
            baseline_net = baseline.avg_income - baseline.avg_expenses
            start_net_worth = await self._get_starting_net_worth(user_id, goal)
            gap = goal.target_value - start_net_worth
            baseline_months = self._estimate_months_to_goal(gap, baseline_net)

        month_date = date.today().replace(day=1)
        candidates = [
            ("Boost income", ACTION_INCOME_DELTA, Decimal("200")),
            ("Reduce expenses", ACTION_EXPENSE_DELTA, Decimal("-200")),
            ("Invest extra", ACTION_INVESTMENT_DELTA, Decimal("200")),
        ]

        opportunities: list[DecisionImpact] = []
        for name, action_type, value in candidates:
            action = StrategyAction(action_type=action_type, value=value, start_date=month_date, end_date=None)
            result = await self._run_with_actions(user_id, goal_id, assumption_id, [action])
            months_saved = None
            if baseline_months is not None:
                if result.time_to_goal_months is None:
                    months_saved = 0
                else:
                    months_saved = baseline_months - result.time_to_goal_months
            efficiency = None
            if months_saved is not None and value != 0:
                efficiency = float(months_saved / (abs(value) / Decimal("100")))
            opportunities.append(
                DecisionImpact(
                    name=name,
                    action_type=action_type,
                    monthly_delta=value,
                    months_saved=months_saved,
                    efficiency_score=efficiency,
                )
            )

        opportunities.sort(key=lambda item: (item.months_saved or 0), reverse=True)

        impact_score = 0
        best_saved = max((item.months_saved or 0 for item in opportunities), default=0)
        if baseline_months:
            impact_score = float(min(100, max(0, best_saved / baseline_months * 100)))

        recommendations = self._build_recommendations(opportunities)
        return DecisionOverview(
            decision_impact_score=impact_score,
            opportunities=opportunities,
            recommendations=recommendations,
        )

    async def get_alert(self, user_id: int, goal_id: int | None = None, assumption_id: int | None = None) -> StrategyAlert:
        baseline = await self._get_cashflow_baseline(user_id)
        if baseline.avg_income <= 0 and baseline.avg_expenses <= 0:
            return StrategyAlert(deviation_score=None, expected_net_worth=None, actual_net_worth=None, message=None)

        net_worth_summary = await self.net_worth_service.get_net_worth_summary(user_id)
        actual_monthly_net = baseline.current_income - baseline.current_expenses
        expected_monthly_net = baseline.avg_income - baseline.avg_expenses

        expected_net = net_worth_summary.net_worth + expected_monthly_net
        actual_net = net_worth_summary.net_worth + actual_monthly_net

        deviation = None
        if expected_monthly_net != 0:
            deviation = float((actual_monthly_net - expected_monthly_net) / expected_monthly_net * 100)

        message = None
        if deviation is not None and deviation < -15:
            message = "Cashflow is tracking below the plan. Consider adjusting expenses or income targets."

        return StrategyAlert(
            deviation_score=deviation,
            expected_net_worth=expected_net,
            actual_net_worth=actual_net,
            message=message,
        )

    async def get_strategy_kpis(
        self, user_id: int, monthly_income: Decimal, monthly_net: Decimal
    ) -> dict:
        goal = await self._resolve_goal(user_id, None)
        if not goal:
            return {}

        start_date = date.today().replace(day=1)
        months_to_target = self._months_from_goal(start_date, goal)
        start_net_worth = await self._get_starting_net_worth(user_id, goal)
        gap = goal.target_value - start_net_worth
        baseline = await self._get_cashflow_baseline(user_id)
        baseline_net = baseline.avg_income - baseline.avg_expenses

        required_savings_rate = None
        required_investment_rate = None

        if months_to_target and monthly_income > 0 and gap > 0:
            required_monthly_savings = gap / Decimal(months_to_target)
            required_savings_rate = float(required_monthly_savings / monthly_income * 100)
            additional_needed = required_monthly_savings - monthly_net
            if additional_needed < 0:
                additional_needed = Decimal("0")
            required_investment_rate = float(additional_needed / monthly_income * 100)

        trajectory = await self.run_trajectory(user_id, TrajectoryRequest(goal_id=goal.id))
        time_to_goal = trajectory.time_to_goal_months
        if time_to_goal is None and months_to_target < 600:
            extended = await self.run_trajectory(
                user_id,
                TrajectoryRequest(goal_id=goal.id, months=600),
            )
            time_to_goal = extended.time_to_goal_months
        if time_to_goal is None:
            time_to_goal = self._estimate_months_to_goal(gap, baseline_net)

        decision_overview = await self.get_decision_overview(user_id, goal.id, None)
        alert = await self.get_alert(user_id, goal.id, None)

        return {
            "time_to_goal_months": time_to_goal,
            "required_savings_rate": required_savings_rate,
            "required_investment_rate": required_investment_rate,
            "trajectory_deviation_score": alert.deviation_score,
            "decision_impact_score": decision_overview.decision_impact_score,
        }

    async def _run_with_actions(
        self,
        user_id: int,
        goal_id: int | None,
        assumption_id: int | None,
        actions: list[StrategyAction],
    ):
        baseline = await self._get_cashflow_baseline(user_id)
        goal = await self._resolve_goal(user_id, goal_id)
        assumptions = await self._resolve_assumptions(user_id, assumption_id)
        start_date = date.today().replace(day=1)
        start_net_worth = await self._get_starting_net_worth(user_id, goal)
        months = self._months_from_goal(start_date, goal)
        return simulate_trajectory(
            start_net_worth=start_net_worth,
            monthly_income=baseline.avg_income,
            monthly_expenses=baseline.avg_expenses,
            assumptions=assumptions,
            actions=actions,
            start_date=start_date,
            months=months,
            target_value=goal.target_value if goal else None,
        )

    def _build_actions(self, scenario_actions, request_actions) -> list[StrategyAction]:
        actions: list[StrategyAction] = []
        for action in scenario_actions or []:
            action_type = action.action_type.value if hasattr(action.action_type, "value") else action.action_type
            actions.append(
                StrategyAction(
                    action_type=action_type,
                    value=Decimal(str(action.value)),
                    start_date=action.start_date,
                    end_date=action.end_date,
                )
            )
        for action in request_actions or []:
            actions.append(
                StrategyAction(
                    action_type=action.action_type.value if hasattr(action.action_type, "value") else action.action_type,
                    value=Decimal(str(action.value)),
                    start_date=action.start_date,
                    end_date=action.end_date,
                )
            )
        return actions

    async def _resolve_goal(self, user_id: int, goal_id: int | None):
        if goal_id:
            goal = await self.goal_repository.get_by_id(goal_id, user_id)
            if not goal:
                raise ValueError("Goal not found")
            return goal
        return await self.goal_repository.get_active_goal(user_id)

    async def _resolve_assumptions(self, user_id: int, assumption_id: int | None) -> StrategyAssumptions:
        assumption = None
        if assumption_id:
            assumption = await self.assumption_repository.get_by_id(assumption_id, user_id)
            if not assumption:
                raise ValueError("Assumption not found")
        else:
            assumption = await self.assumption_repository.get_active(user_id)

        if not assumption:
            return StrategyAssumptions(
                income_growth_rate=Decimal("0"),
                expense_inflation_rate=Decimal("0"),
                investment_return_rate=Decimal("0"),
                volatility=Decimal("0"),
            )

        return StrategyAssumptions(
            income_growth_rate=Decimal(str(assumption.income_growth_rate)),
            expense_inflation_rate=Decimal(str(assumption.expense_inflation_rate)),
            investment_return_rate=Decimal(str(assumption.investment_return_rate)),
            volatility=Decimal(str(assumption.volatility)),
        )

    async def _get_starting_net_worth(self, user_id: int, goal) -> Decimal:
        summary = await self.net_worth_service.get_net_worth_summary(user_id)
        if goal and goal.target_type == GoalType.LIQUID_ASSETS:
            liquid_types = {
                AccountType.CASH.value,
                AccountType.SAVINGS.value,
                AccountType.CHECKING.value,
                AccountType.INVESTMENT.value,
            }
            total = Decimal("0")
            for key, value in summary.breakdown.items():
                if key in liquid_types:
                    total += Decimal(str(value))
            return total
        return Decimal(str(summary.net_worth))

    async def _get_cashflow_baseline(self, user_id: int, months: int = 6) -> CashflowBaseline:
        end = datetime.utcnow()
        start = end - timedelta(days=30 * months)

        income_case = case((Transaction.amount > 0, Transaction.amount), else_=0)
        expense_case = case((Transaction.amount < 0, Transaction.amount), else_=0)

        result = await self.session.execute(
            select(
                func.date_trunc("month", Transaction.transaction_date).label("month"),
                func.sum(income_case).label("income"),
                func.sum(expense_case).label("expenses"),
            )
            .where(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= start,
            )
            .group_by("month")
            .order_by("month")
        )

        rows = result.all()
        if not rows:
            return CashflowBaseline(
                avg_income=Decimal("0"),
                avg_expenses=Decimal("0"),
                current_income=Decimal("0"),
                current_expenses=Decimal("0"),
            )

        income_total = Decimal("0")
        expense_total = Decimal("0")
        for row in rows:
            income_total += Decimal(str(row.income or 0))
            expense_total += Decimal(str(abs(row.expenses or 0)))

        avg_income = income_total / Decimal(len(rows))
        avg_expenses = expense_total / Decimal(len(rows))

        current = rows[-1]
        current_income = Decimal(str(current.income or 0))
        current_expenses = Decimal(str(abs(current.expenses or 0)))

        return CashflowBaseline(
            avg_income=avg_income,
            avg_expenses=avg_expenses,
            current_income=current_income,
            current_expenses=current_expenses,
        )

    def _months_from_goal(self, start_date: date, goal) -> int:
        if not goal or not goal.target_date:
            return 120
        months = (goal.target_date.year - start_date.year) * 12 + (goal.target_date.month - start_date.month)
        return max(1, min(600, months))

    def _estimate_months_to_goal(self, gap: Decimal, monthly_net: Decimal) -> int | None:
        if gap <= 0:
            return 0
        if monthly_net <= 0:
            return None
        months = (gap / monthly_net).to_integral_value(rounding=ROUND_CEILING)
        return max(1, int(months))

    def _build_recommendations(self, opportunities: Iterable[DecisionImpact]) -> list[DecisionRecommendation]:
        recommendations: list[DecisionRecommendation] = []
        for item in opportunities:
            if item.months_saved and item.months_saved > 0:
                recommendations.append(
                    DecisionRecommendation(
                        headline=f"{item.name} could save ~{item.months_saved} months",
                        detail="Review feasibility and adjust assumptions to validate the impact.",
                    )
                )
        if not recommendations:
            recommendations.append(
                DecisionRecommendation(
                    headline="Your baseline trajectory is stable",
                    detail="Track progress monthly and revisit goals if cashflow changes.",
                )
            )
        return recommendations
