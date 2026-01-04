"""Financial goal service."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.financial_goal import FinancialGoalRepository
from app.schemas.goal import FinancialGoalResponse


class GoalService:
    """Service for financial goals."""

    def __init__(self, session: AsyncSession):
        self.repository = FinancialGoalRepository(session)

    async def get_goal(self, goal_id: int, user_id: int) -> FinancialGoalResponse:
        goal = await self.repository.get_by_id(goal_id, user_id)
        if not goal:
            raise ValueError("Goal not found")
        return FinancialGoalResponse.from_orm(goal)

    async def get_all_goals(self, user_id: int) -> list[FinancialGoalResponse]:
        goals = await self.repository.get_all_by_user(user_id)
        return [FinancialGoalResponse.from_orm(goal) for goal in goals]

    async def get_active_goal(self, user_id: int) -> FinancialGoalResponse | None:
        goal = await self.repository.get_active_goal(user_id)
        return FinancialGoalResponse.from_orm(goal) if goal else None

    async def create_goal(self, user_id: int, **kwargs) -> FinancialGoalResponse:
        goal = await self.repository.create(user_id=user_id, **kwargs)
        return FinancialGoalResponse.from_orm(goal)

    async def update_goal(self, goal_id: int, user_id: int, **kwargs) -> FinancialGoalResponse:
        goal = await self.repository.update(goal_id, user_id, **kwargs)
        if not goal:
            raise ValueError("Goal not found")
        return FinancialGoalResponse.from_orm(goal)

    async def delete_goal(self, goal_id: int, user_id: int) -> bool:
        success = await self.repository.delete(goal_id, user_id)
        if not success:
            raise ValueError("Goal not found")
        return success
