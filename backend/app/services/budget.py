"""Budget service for budget-related business logic."""
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import extract, func, select
from app.repositories.budget import BudgetRepository
from app.models.budget import Budget
from app.models.transaction import Transaction
from app.schemas.budget import BudgetResponse, BudgetWithSpent


class BudgetService:
    """Service for budget operations."""
    
    def __init__(self, session: AsyncSession):
        self.repository = BudgetRepository(session)
        self.session = session
    
    async def get_budget(self, budget_id: int, user_id: int) -> BudgetResponse:
        """Get budget by ID."""
        budget = await self.repository.get_by_id(budget_id, user_id)
        if not budget:
            raise ValueError("Budget not found")
        return BudgetResponse.from_orm(budget)
    
    async def get_all_budgets(self, user_id: int) -> list[BudgetResponse]:
        """Get all budgets for user."""
        budgets = await self.repository.get_all_by_user(user_id)
        return [BudgetResponse.from_orm(b) for b in budgets]
    
    async def get_budgets_with_spent(self, user_id: int, month) -> list[BudgetWithSpent]:
        """Get budgets with spent amounts for a month."""
        budgets = await self.repository.get_by_month(user_id, month)
        result = []
        
        for budget in budgets:
            spent = await self._get_spent_amount(budget.category_id, month.year, month.month)
            remaining = budget.amount - spent
            percentage = (float(spent) / float(budget.amount) * 100) if budget.amount > 0 else 0
            
            result.append(
                BudgetWithSpent(
                    id=budget.id,
                    category_id=budget.category_id,
                    category_name=budget.category.name,
                    amount=budget.amount,
                    spent=spent,
                    remaining=remaining,
                    percentage_used=percentage,
                    month=budget.month,
                )
            )
        
        return result
    
    async def create_budget(self, user_id: int, **kwargs) -> BudgetResponse:
        """Create a new budget."""
        budget = await self.repository.create(user_id=user_id, **kwargs)
        return BudgetResponse.from_orm(budget)
    
    async def update_budget(self, budget_id: int, user_id: int, **kwargs) -> BudgetResponse:
        """Update budget."""
        budget = await self.repository.update(budget_id, user_id, **kwargs)
        if not budget:
            raise ValueError("Budget not found")
        return BudgetResponse.from_orm(budget)
    
    async def delete_budget(self, budget_id: int, user_id: int) -> bool:
        """Delete budget."""
        success = await self.repository.delete(budget_id, user_id)
        if not success:
            raise ValueError("Budget not found")
        return success
    
    async def _get_spent_amount(self, category_id: int, year: int, month: int) -> Decimal:
        """Get total spent in a category for a month."""
        result = await self.session.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.category_id == category_id,
                extract('year', Transaction.transaction_date) == year,
                extract('month', Transaction.transaction_date) == month,
                Transaction.amount < 0,
            )
        )
        total = result.scalar() or 0
        return Decimal(str(abs(float(total))))
