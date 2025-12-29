"""Dashboard service for KPIs and analytics."""
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, extract, func
from app.models.transaction import Transaction
from app.models.account import Account
from app.schemas.dashboard import DashboardKPI, DashboardData
from app.services.net_worth import NetWorthService
from app.models.category import Category
from app.models.budget import Budget


class DashboardService:
    """Service for dashboard analytics."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.net_worth_service = NetWorthService(session)
    
    async def get_dashboard_data(self, user_id: int) -> DashboardData:
        """Get complete dashboard data."""
        today = datetime.now()
        
        # Calculate KPIs
        monthly_expenses = await self._get_monthly_expenses(user_id, today.year, today.month)
        burn_rate = await self._calculate_burn_rate(user_id)
        net_worth_summary = await self.net_worth_service.get_net_worth_summary(user_id)
        
        kpi = DashboardKPI(
            monthly_expenses=monthly_expenses,
            burn_rate=burn_rate,
            current_net_worth=net_worth_summary.net_worth,
        )
        
        # Get expenses by category
        expenses_by_category = await self._get_expenses_by_category(user_id, today.year, today.month)
        
        # Get monthly expenses for last 6 months
        monthly_expenses_history = await self._get_monthly_expenses_history(user_id)
        
        # Get recent transactions
        recent_transactions = await self._get_recent_transactions(user_id, limit=10)

        onboarding = await self._get_onboarding_steps(user_id)
        
        return DashboardData(
            kpi=kpi,
            expenses_by_category=expenses_by_category,
            monthly_expenses=monthly_expenses_history,
            recent_transactions=recent_transactions,
            onboarding=onboarding,
        )
    
    async def _get_monthly_expenses(self, user_id: int, year: int, month: int) -> Decimal:
        """Get total expenses for a month."""
        result = await self.session.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.user_id == user_id,
                extract('year', Transaction.transaction_date) == year,
                extract('month', Transaction.transaction_date) == month,
                Transaction.amount < 0,
            )
        )
        total = result.scalar() or 0
        return Decimal(str(abs(float(total))))
    
    async def _calculate_burn_rate(self, user_id: int) -> Decimal:
        """Calculate burn rate (average daily expenses for last 30 days)."""
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        result = await self.session.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= thirty_days_ago,
                Transaction.amount < 0,
            )
        )
        total = result.scalar() or 0
        daily_rate = abs(float(total)) / 30
        return Decimal(str(daily_rate))
    
    async def _get_expenses_by_category(self, user_id: int, year: int, month: int):
        """Get expenses grouped by category."""
        result = await self.session.execute(
            select(
                Category.id,
                Category.name,
                func.sum(Transaction.amount).label('amount')
            ).join(Transaction).where(
                Transaction.user_id == user_id,
                extract('year', Transaction.transaction_date) == year,
                extract('month', Transaction.transaction_date) == month,
                Transaction.amount < 0,
            ).group_by(Category.id, Category.name)
        )
        
        rows = result.all()
        
        # Calculate total for percentages
        total = sum(abs(float(row[2])) for row in rows if row[2])
        
        from app.schemas.dashboard import CategoryExpense
        
        expenses = []
        for category_id, category_name, amount in rows:
            if amount:
                percentage = abs(float(amount)) / total * 100 if total > 0 else 0
                expenses.append(
                    CategoryExpense(
                        category_id=category_id,
                        category_name=category_name,
                        amount=Decimal(str(abs(float(amount)))),
                        percentage=percentage,
                    )
                )
        
        return sorted(expenses, key=lambda x: x.amount, reverse=True)
    
    async def _get_monthly_expenses_history(self, user_id: int, months: int = 6):
        """Get monthly expenses for the last N months."""
        from app.schemas.dashboard import MonthlyExpense
        
        expenses = []
        now = datetime.now()
        
        for i in range(months):
            date = now - timedelta(days=30 * i)
            monthly_total = await self._get_monthly_expenses(user_id, date.year, date.month)
            
            expenses.append(
                MonthlyExpense(
                    month=date.strftime("%Y-%m"),
                    total=monthly_total,
                )
            )
        
        return list(reversed(expenses))
    
    async def _get_recent_transactions(self, user_id: int, limit: int = 10):
        """Get recent transactions."""
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.transaction_date.desc())
            .limit(limit)
        )
        
        transactions = result.scalars().all()
        
        return [
            {
                "id": t.id,
                "description": t.description,
                "amount": float(t.amount),
                "date": t.transaction_date.isoformat(),
                "category_id": t.category_id,
            }
            for t in transactions
        ]

    async def _get_onboarding_steps(self, user_id: int) -> list[dict]:
        """Compute onboarding progress."""
        account_count = await self.session.scalar(
            select(func.count(Account.id)).where(Account.user_id == user_id)
        )
        category_count = await self.session.scalar(
            select(func.count(Category.id)).where(Category.user_id == user_id)
        )
        transaction_count = await self.session.scalar(
            select(func.count(Transaction.id)).where(Transaction.user_id == user_id)
        )
        budget_count = await self.session.scalar(
            select(func.count(Budget.id)).where(Budget.user_id == user_id)
        )

        return [
            {"key": "add_account", "label": "Add an account", "completed": (account_count or 0) > 0},
            {"key": "add_category", "label": "Create categories", "completed": (category_count or 0) > 0},
            {"key": "add_transaction", "label": "Add a transaction", "completed": (transaction_count or 0) > 0},
            {"key": "set_budget", "label": "Set a budget", "completed": (budget_count or 0) > 0},
        ]
