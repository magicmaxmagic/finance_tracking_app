"""Dashboard service for KPIs and analytics."""
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, extract, func
from app.models.transaction import Transaction
from app.models.account import Account, AccountType
from app.schemas.dashboard import DashboardKPI, DashboardData
from app.services.net_worth import NetWorthService
from app.services.strategy import StrategyService
from app.models.onboarding import OnboardingProfile
from app.models.category import Category
from app.models.budget import Budget
from app.models.investment import InvestmentAsset


class DashboardService:
    """Service for dashboard analytics."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.net_worth_service = NetWorthService(session)
    
    async def get_dashboard_data(self, user_id: int) -> DashboardData:
        """Get complete dashboard data."""
        today = datetime.now()
        reference_date = await self._get_reference_date(user_id, today)
        reference_year = reference_date.year
        reference_month = reference_date.month

        cashflow_history = await self._get_monthly_cashflow_history(user_id, anchor_date=reference_date)
        if cashflow_history:
            current_cashflow = cashflow_history[-1]
            monthly_income = current_cashflow.income
            monthly_expenses = current_cashflow.expenses
            monthly_net = current_cashflow.net
        else:
            monthly_income = await self._get_monthly_income(user_id, reference_year, reference_month)
            monthly_expenses = await self._get_monthly_expenses(user_id, reference_year, reference_month)
            monthly_net = monthly_income - monthly_expenses

        previous_cashflow = cashflow_history[-2] if len(cashflow_history) >= 2 else None
        income_change_pct = self._calculate_change_pct(
            monthly_income, previous_cashflow.income if previous_cashflow else Decimal("0")
        )
        expense_change_pct = self._calculate_change_pct(
            monthly_expenses, previous_cashflow.expenses if previous_cashflow else Decimal("0")
        )
        net_change_pct = self._calculate_change_pct(
            monthly_net, previous_cashflow.net if previous_cashflow else Decimal("0")
        )

        avg_monthly_income = (
            sum((entry.income for entry in cashflow_history), Decimal("0")) / len(cashflow_history)
            if cashflow_history
            else Decimal("0")
        )
        avg_monthly_expenses = (
            sum((entry.expenses for entry in cashflow_history), Decimal("0")) / len(cashflow_history)
            if cashflow_history
            else Decimal("0")
        )

        savings_rate = float(monthly_net / monthly_income * 100) if monthly_income > 0 else 0.0
        burn_rate = await self._calculate_burn_rate(user_id)
        net_worth_summary = await self.net_worth_service.get_net_worth_summary(user_id)

        strategy_service = StrategyService(self.session)
        strategy_kpis = await strategy_service.get_strategy_kpis(
            user_id=user_id,
            monthly_income=monthly_income,
            monthly_net=monthly_net,
        )

        kpi = DashboardKPI(
            monthly_income=monthly_income,
            monthly_expenses=monthly_expenses,
            monthly_net=monthly_net,
            savings_rate=savings_rate,
            burn_rate=burn_rate,
            current_net_worth=net_worth_summary.net_worth,
            avg_monthly_income=avg_monthly_income,
            avg_monthly_expenses=avg_monthly_expenses,
            income_change_pct=income_change_pct,
            expense_change_pct=expense_change_pct,
            net_change_pct=net_change_pct,
            time_to_goal_months=strategy_kpis.get("time_to_goal_months"),
            required_savings_rate=strategy_kpis.get("required_savings_rate"),
            required_investment_rate=strategy_kpis.get("required_investment_rate"),
            trajectory_deviation_score=strategy_kpis.get("trajectory_deviation_score"),
            decision_impact_score=strategy_kpis.get("decision_impact_score"),
        )
        
        # Get expenses by category
        expenses_by_category = await self._get_expenses_by_category(user_id, reference_year, reference_month)
        assets_by_category = await self._get_assets_by_category(user_id)

        expenses_by_label = await self._get_expenses_by_label(user_id, reference_year, reference_month)
        income_by_label = await self._get_income_by_label(user_id, reference_year, reference_month)

        # Get monthly expenses for last 6 months
        from app.schemas.dashboard import MonthlyExpense
        monthly_expenses_history = [
            MonthlyExpense(month=entry.month, total=entry.expenses) for entry in cashflow_history
        ]

        # Get recent transactions
        recent_transactions = await self._get_recent_transactions(user_id, limit=10)

        onboarding = await self._get_onboarding_steps(user_id)
        top_expense_merchants = await self._get_top_merchants(
            user_id, reference_year, reference_month, "expense"
        )
        top_income_merchants = await self._get_top_merchants(
            user_id, reference_year, reference_month, "income"
        )
        
        return DashboardData(
            kpi=kpi,
            expenses_by_category=expenses_by_category,
            assets_by_category=assets_by_category,
            monthly_expenses=monthly_expenses_history,
            cashflow=cashflow_history,
            recent_transactions=recent_transactions,
            onboarding=onboarding,
            expenses_by_label=expenses_by_label,
            income_by_label=income_by_label,
            top_expense_merchants=top_expense_merchants,
            top_income_merchants=top_income_merchants,
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

    async def _get_monthly_income(self, user_id: int, year: int, month: int) -> Decimal:
        """Get total income for a month."""
        result = await self.session.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.user_id == user_id,
                extract('year', Transaction.transaction_date) == year,
                extract('month', Transaction.transaction_date) == month,
                Transaction.amount > 0,
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

    async def _get_assets_by_category(self, user_id: int):
        """Get asset allocation by category across accounts and investments."""
        account_labels = {
            "cash": "Cash",
            "savings": "Savings",
            "checking": "Checking",
            "investment": "Investment accounts",
            "other": "Other accounts",
        }
        investment_labels = {
            "rental": "Rental",
            "stocks": "Stocks",
            "funds": "Funds",
            "crypto": "Crypto",
            "portfolio": "Portfolio",
            "business": "Business",
            "other": "Other investments",
        }

        totals: dict[str, Decimal] = {}
        labels: dict[str, str] = {}

        account_result = await self.session.execute(
            select(Account).where(
                Account.user_id == user_id,
                Account.is_active == True,
            )
        )
        accounts = account_result.scalars().all()

        for account in accounts:
            if account.account_type in {AccountType.DEBT, AccountType.CREDIT}:
                continue
            balance = account.balance or Decimal("0")
            balance = abs(balance)
            key = f"account:{account.account_type.value}"
            label = account_labels.get(account.account_type.value, account.account_type.value.title())
            totals[key] = totals.get(key, Decimal("0")) + balance
            labels[key] = label

        investment_result = await self.session.execute(
            select(InvestmentAsset).where(
                InvestmentAsset.user_id == user_id,
                InvestmentAsset.is_active == True,
            )
        )
        investments = investment_result.scalars().all()
        for investment in investments:
            value = investment.current_value or Decimal("0")
            key = f"investment:{investment.category.value}"
            label = investment_labels.get(investment.category.value, investment.category.value.title())
            totals[key] = totals.get(key, Decimal("0")) + value
            labels[key] = label

        total_value = sum(totals.values(), Decimal("0"))
        from app.schemas.dashboard import AssetCategory

        items = [
            AssetCategory(
                key=key,
                label=labels.get(key, key),
                amount=amount,
                percentage=(float(amount / total_value * 100) if total_value > 0 else 0.0),
            )
            for key, amount in totals.items()
            if amount > 0
        ]
        return sorted(items, key=lambda item: item.amount, reverse=True)

    async def _get_expenses_by_label(self, user_id: int, year: int, month: int):
        """Get expenses grouped by labels (tags)."""
        result = await self.session.execute(
            select(Transaction.tags, func.sum(Transaction.amount).label('amount')).where(
                Transaction.user_id == user_id,
                Transaction.tags.isnot(None),
                Transaction.tags != "",
                extract('year', Transaction.transaction_date) == year,
                extract('month', Transaction.transaction_date) == month,
                Transaction.amount < 0,
            ).group_by(Transaction.tags)
        )

        rows = result.all()
        label_totals = {}
        for tags, amount in rows:
            if not tags or not amount:
                continue
            for label in [t.strip() for t in tags.split(",") if t.strip()]:
                label_totals[label] = label_totals.get(label, 0) + abs(float(amount))

        total = sum(label_totals.values())
        from app.schemas.dashboard import LabelExpense

        expenses = [
            LabelExpense(
                label=label,
                amount=Decimal(str(amount)),
                percentage=(amount / total * 100) if total > 0 else 0,
            )
            for label, amount in label_totals.items()
        ]
        return sorted(expenses, key=lambda x: x.amount, reverse=True)

    async def _get_income_by_label(self, user_id: int, year: int, month: int):
        """Get income grouped by labels (tags)."""
        result = await self.session.execute(
            select(Transaction.tags, func.sum(Transaction.amount).label('amount')).where(
                Transaction.user_id == user_id,
                Transaction.tags.isnot(None),
                Transaction.tags != "",
                extract('year', Transaction.transaction_date) == year,
                extract('month', Transaction.transaction_date) == month,
                Transaction.amount > 0,
            ).group_by(Transaction.tags)
        )

        rows = result.all()
        label_totals = {}
        for tags, amount in rows:
            if not tags or not amount:
                continue
            for label in [t.strip() for t in tags.split(",") if t.strip()]:
                label_totals[label] = label_totals.get(label, 0) + abs(float(amount))

        total = sum(label_totals.values())
        from app.schemas.dashboard import LabelExpense

        expenses = [
            LabelExpense(
                label=label,
                amount=Decimal(str(amount)),
                percentage=(amount / total * 100) if total > 0 else 0,
            )
            for label, amount in label_totals.items()
        ]
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

    async def _get_monthly_cashflow_history(
        self, user_id: int, months: int = 6, anchor_date: datetime | None = None
    ):
        """Get monthly cashflow for the last N months."""
        from app.schemas.dashboard import MonthlyCashflow

        history = []
        now = anchor_date or datetime.now()

        for i in range(months):
            date = now - timedelta(days=30 * i)
            income = await self._get_monthly_income(user_id, date.year, date.month)
            expenses = await self._get_monthly_expenses(user_id, date.year, date.month)
            net = income - expenses
            history.append(
                MonthlyCashflow(
                    month=date.strftime("%Y-%m"),
                    income=income,
                    expenses=expenses,
                    net=net,
                )
            )

        return list(reversed(history))

    async def _get_reference_date(self, user_id: int, fallback: datetime) -> datetime:
        """Get the most recent transaction date for anchoring dashboard metrics."""
        result = await self.session.execute(
            select(func.max(Transaction.transaction_date)).where(Transaction.user_id == user_id)
        )
        latest = result.scalar()
        return latest or fallback

    async def _get_top_merchants(self, user_id: int, year: int, month: int, direction: str):
        """Get top merchants/sources for a month."""
        from app.schemas.dashboard import TopMerchant

        amount_expr = func.sum(func.abs(Transaction.amount))
        filters = [
            Transaction.user_id == user_id,
            extract("year", Transaction.transaction_date) == year,
            extract("month", Transaction.transaction_date) == month,
        ]
        if direction == "expense":
            filters.append(Transaction.amount < 0)
        else:
            filters.append(Transaction.amount > 0)

        result = await self.session.execute(
            select(
                Transaction.description,
                amount_expr.label("amount"),
                func.count(Transaction.id).label("count"),
            )
            .where(*filters)
            .group_by(Transaction.description)
            .order_by(amount_expr.desc())
            .limit(5)
        )

        rows = result.all()
        return [
            TopMerchant(
                name=row[0] or "Unlabeled",
                amount=Decimal(str(float(row[1] or 0))),
                count=int(row[2] or 0),
            )
            for row in rows
        ]

    def _calculate_change_pct(self, current: Decimal, previous: Decimal) -> float:
        """Calculate month-over-month percentage change."""
        if previous == 0:
            return 0.0
        return float((current - previous) / previous * 100)
    
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
        onboarding_completed = await self.session.scalar(
            select(func.count(OnboardingProfile.id)).where(
                OnboardingProfile.user_id == user_id,
                OnboardingProfile.is_completed == True,
            )
        )
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
            {
                "key": "complete_onboarding",
                "label": "Complete investor onboarding",
                "completed": onboarding_completed,
            },
            {"key": "add_account", "label": "Add an account", "completed": (account_count or 0) > 0},
            {"key": "add_category", "label": "Create categories", "completed": (category_count or 0) > 0},
            {"key": "add_transaction", "label": "Add a transaction", "completed": (transaction_count or 0) > 0},
            {"key": "set_budget", "label": "Set a budget", "completed": (budget_count or 0) > 0},
        ]
