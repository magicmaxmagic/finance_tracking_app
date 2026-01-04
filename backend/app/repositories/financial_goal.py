"""Repository for financial goals."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.financial_goal import FinancialGoal, GoalStatus


class FinancialGoalRepository:
    """Financial goal repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, goal_id: int, user_id: int) -> FinancialGoal | None:
        result = await self.session.execute(
            select(FinancialGoal).where(
                FinancialGoal.id == goal_id,
                FinancialGoal.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_by_user(self, user_id: int) -> list[FinancialGoal]:
        result = await self.session.execute(
            select(FinancialGoal)
            .where(FinancialGoal.user_id == user_id)
            .order_by(FinancialGoal.target_date)
        )
        return list(result.scalars().all())

    async def get_active_goal(self, user_id: int) -> FinancialGoal | None:
        result = await self.session.execute(
            select(FinancialGoal)
            .where(
                FinancialGoal.user_id == user_id,
                FinancialGoal.status == GoalStatus.ACTIVE,
            )
            .order_by(FinancialGoal.target_date)
        )
        return result.scalars().first()

    async def create(self, user_id: int, **kwargs) -> FinancialGoal:
        goal = FinancialGoal(user_id=user_id, **kwargs)
        self.session.add(goal)
        await self.session.commit()
        await self.session.refresh(goal)
        return goal

    async def update(self, goal_id: int, user_id: int, **kwargs) -> FinancialGoal | None:
        goal = await self.get_by_id(goal_id, user_id)
        if not goal:
            return None
        for key, value in kwargs.items():
            if value is not None:
                setattr(goal, key, value)
        self.session.add(goal)
        await self.session.commit()
        await self.session.refresh(goal)
        return goal

    async def delete(self, goal_id: int, user_id: int) -> bool:
        goal = await self.get_by_id(goal_id, user_id)
        if not goal:
            return False
        await self.session.delete(goal)
        await self.session.commit()
        return True
