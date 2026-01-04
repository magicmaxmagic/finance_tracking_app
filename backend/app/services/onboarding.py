"""Onboarding service for investor profiling."""
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.onboarding import RiskAppetite, InvestorProfile
from app.repositories.onboarding import OnboardingRepository
from app.repositories.financial_goal import FinancialGoalRepository
from app.repositories.assumption import AssumptionRepository
from app.schemas.onboarding import OnboardingProfileResponse


RISK_RETURN_MAP = {
    RiskAppetite.LOW: Decimal("3.0"),
    RiskAppetite.MEDIUM: Decimal("5.0"),
    RiskAppetite.HIGH: Decimal("7.0"),
}

RISK_VOL_MAP = {
    RiskAppetite.LOW: Decimal("2.0"),
    RiskAppetite.MEDIUM: Decimal("4.0"),
    RiskAppetite.HIGH: Decimal("6.0"),
}


class OnboardingService:
    """Service for onboarding data."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = OnboardingRepository(session)
        self.goal_repository = FinancialGoalRepository(session)
        self.assumption_repository = AssumptionRepository(session)

    async def get_status(self, user_id: int) -> bool:
        profile = await self.repository.get_by_user(user_id)
        return bool(profile and profile.is_completed)

    async def get_profile(self, user_id: int) -> OnboardingProfileResponse | None:
        profile = await self.repository.get_by_user(user_id)
        return OnboardingProfileResponse.from_orm(profile) if profile else None

    async def complete_onboarding(self, user_id: int, payload) -> OnboardingProfileResponse:
        target_date = self._compute_target_date(payload.goal_horizon_years)
        profile = await self.repository.get_by_user(user_id)
        data = {
            "risk_appetite": RiskAppetite(payload.risk_appetite),
            "investor_profile": InvestorProfile(payload.investor_profile),
            "goal_value": payload.goal_value,
            "goal_horizon_years": payload.goal_horizon_years,
            "target_date": target_date,
            "asset_allocation": payload.asset_allocation,
            "investment_interests": payload.investment_interests,
            "vision": payload.vision,
            "is_completed": True,
            "completed_at": datetime.utcnow(),
        }

        if profile:
            profile = await self.repository.update(profile, **data)
        else:
            profile = await self.repository.create(user_id=user_id, **data)

        await self._sync_goal(user_id, payload.goal_value, target_date)
        await self._sync_assumptions(user_id, RiskAppetite(payload.risk_appetite))

        return OnboardingProfileResponse.from_orm(profile)

    def _compute_target_date(self, horizon_years: int) -> date:
        today = date.today()
        target_year = today.year + horizon_years
        return date(target_year, today.month, 1)

    async def _sync_goal(self, user_id: int, goal_value: Decimal, target_date: date) -> None:
        goal = await self.goal_repository.get_active_goal(user_id)
        if goal:
            await self.goal_repository.update(
                goal.id,
                user_id,
                target_value=goal_value,
                target_date=target_date,
            )
            return
        await self.goal_repository.create(
            user_id=user_id,
            name="Primary goal",
            target_type="net_worth",
            target_value=goal_value,
            target_date=target_date,
            status="active",
        )

    async def _sync_assumptions(self, user_id: int, risk_appetite: RiskAppetite) -> None:
        latest = await self.assumption_repository.get_latest_version(user_id)
        next_version = (latest.version + 1) if latest else 1
        await self.assumption_repository.deactivate_all(user_id)
        await self.assumption_repository.create(
            user_id=user_id,
            name="Onboarding assumptions",
            version=next_version,
            income_growth_rate=Decimal("2.0"),
            expense_inflation_rate=Decimal("3.0"),
            investment_return_rate=RISK_RETURN_MAP[risk_appetite],
            volatility=RISK_VOL_MAP[risk_appetite],
            risk_level=risk_appetite.value,
            is_active=True,
        )
