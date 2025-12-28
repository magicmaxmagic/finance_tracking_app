"""Budget repository for database operations."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date
from app.models.budget import Budget


class BudgetRepository:
    """Repository for budget operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, budget_id: int, user_id: int) -> Budget | None:
        """Get budget by ID (ensure user ownership)."""
        result = await self.session.execute(
            select(Budget).where(
                Budget.id == budget_id,
                Budget.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_all_by_user(self, user_id: int) -> list[Budget]:
        """Get all budgets for user."""
        result = await self.session.execute(
            select(Budget).where(Budget.user_id == user_id).order_by(Budget.month.desc())
        )
        return list(result.scalars().all())
    
    async def get_by_month(self, user_id: int, month: date) -> list[Budget]:
        """Get budgets for a specific month."""
        result = await self.session.execute(
            select(Budget).where(
                Budget.user_id == user_id,
                Budget.month == month
            ).order_by(Budget.created_at)
        )
        return list(result.scalars().all())
    
    async def get_or_create(
        self, user_id: int, category_id: int, month: date, amount: float
    ) -> Budget:
        """Get existing budget or create new one."""
        result = await self.session.execute(
            select(Budget).where(
                Budget.user_id == user_id,
                Budget.category_id == category_id,
                Budget.month == month
            )
        )
        budget = result.scalar_one_or_none()
        
        if not budget:
            budget = Budget(
                user_id=user_id,
                category_id=category_id,
                month=month,
                amount=amount
            )
            self.session.add(budget)
            await self.session.commit()
            await self.session.refresh(budget)
        
        return budget
    
    async def create(self, user_id: int, **kwargs) -> Budget:
        """Create a new budget."""
        budget = Budget(user_id=user_id, **kwargs)
        self.session.add(budget)
        await self.session.commit()
        await self.session.refresh(budget)
        return budget
    
    async def update(self, budget_id: int, user_id: int, **kwargs) -> Budget | None:
        """Update budget."""
        budget = await self.get_by_id(budget_id, user_id)
        if not budget:
            return None
        
        for key, value in kwargs.items():
            if value is not None:
                setattr(budget, key, value)
        
        self.session.add(budget)
        await self.session.commit()
        await self.session.refresh(budget)
        return budget
    
    async def delete(self, budget_id: int, user_id: int) -> bool:
        """Delete budget."""
        budget = await self.get_by_id(budget_id, user_id)
        if not budget:
            return False
        
        await self.session.delete(budget)
        await self.session.commit()
        return True
