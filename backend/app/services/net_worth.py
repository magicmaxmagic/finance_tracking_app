"""Net worth service for net worth calculations."""
from decimal import Decimal
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.repositories.net_worth import NetWorthSnapshotRepository
from app.models.account import Account, AccountType
from app.models.transaction import Transaction
from app.models.investment import InvestmentAsset
from app.models.net_worth_snapshot import NetWorthSnapshot
from app.schemas.net_worth import NetWorthSummary


class NetWorthService:
    """Service for net worth operations."""
    
    def __init__(self, session: AsyncSession):
        self.repository = NetWorthSnapshotRepository(session)
        self.session = session
    
    async def create_snapshot(self, user_id: int, **kwargs) -> NetWorthSnapshot:
        """Create a new net worth snapshot."""
        snapshot = await self.repository.create(user_id=user_id, **kwargs)
        return snapshot
    
    async def get_net_worth_summary(self, user_id: int) -> NetWorthSummary:
        """Get current net worth summary."""
        # Get all accounts
        result = await self.session.execute(
            select(Account).where(Account.user_id == user_id, Account.is_active == True)
        )
        accounts = result.scalars().all()

        transaction_totals: dict[int, Decimal] = {}
        if accounts:
            tx_result = await self.session.execute(
                select(
                    Transaction.account_id,
                    func.sum(Transaction.amount).label("total"),
                )
                .where(Transaction.user_id == user_id)
                .group_by(Transaction.account_id)
            )
            transaction_totals = {
                account_id: Decimal(str(total or 0))
                for account_id, total in tx_result.all()
            }
        
        total_assets = Decimal("0")
        total_liabilities = Decimal("0")
        breakdown: dict[str, Decimal] = {}

        account_labels = {
            "cash": "Cash",
            "savings": "Savings",
            "checking": "Checking",
            "investment": "Investment accounts",
            "debt": "Debt",
            "credit": "Credit",
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
        
        for account in accounts:
            balance = account.balance or Decimal("0")
            if balance == 0:
                tx_total = transaction_totals.get(account.id, Decimal("0"))
                if tx_total != 0:
                    balance = tx_total
            account_type = account.account_type
            
            # Categorize as asset or liability
            if account_type in [AccountType.DEBT, AccountType.CREDIT]:
                total_liabilities += abs(balance) if balance < 0 else balance
            else:
                total_assets += balance
            
            # Build breakdown
            label = account_labels.get(account_type.value, account_type.value.title())
            if label not in breakdown:
                breakdown[label] = Decimal("0")
            breakdown[label] += balance

        investment_result = await self.session.execute(
            select(InvestmentAsset).where(
                InvestmentAsset.user_id == user_id,
                InvestmentAsset.is_active == True,
            )
        )
        investments = investment_result.scalars().all()
        for investment in investments:
            value = investment.current_value or Decimal("0")
            total_assets += value
            label = investment_labels.get(investment.category.value, investment.category.value.title())
            breakdown_label = f"Investments - {label}"
            if breakdown_label not in breakdown:
                breakdown[breakdown_label] = Decimal("0")
            breakdown[breakdown_label] += value
        
        net_worth = total_assets - total_liabilities
        
        return NetWorthSummary(
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            net_worth=net_worth,
            breakdown=breakdown,
            date=date.today(),
        )
    
    async def get_net_worth_history(
        self, user_id: int, start_date: date, end_date: date
    ) -> list[dict]:
        """Get net worth history for a date range."""
        snapshots = await self.repository.get_by_date_range(user_id, start_date, end_date)
        
        # Group by date and sum
        data = {}
        for snapshot in snapshots:
            date_key = snapshot.snapshot_date
            if date_key not in data:
                data[date_key] = Decimal("0")
            data[date_key] += snapshot.balance
        
        return [
            {"date": d, "net_worth": float(v)}
            for d, v in sorted(data.items())
        ]

    async def capture_snapshot(self, user_id: int, snapshot_date: date | None = None) -> dict:
        """Capture net worth snapshot for all active accounts."""
        target_date = snapshot_date or date.today()

        result = await self.session.execute(
            select(Account).where(Account.user_id == user_id, Account.is_active == True)
        )
        accounts = result.scalars().all()

        created = 0
        updated = 0

        for account in accounts:
            existing = await self.repository.get_by_account_and_date(
                account_id=account.id,
                user_id=user_id,
                snapshot_date=target_date,
            )
            if existing:
                existing.balance = account.balance
                updated += 1
            else:
                snapshot = NetWorthSnapshot(
                    user_id=user_id,
                    account_id=account.id,
                    snapshot_date=target_date,
                    balance=account.balance,
                )
                self.session.add(snapshot)
                created += 1

        await self.session.commit()

        return {
            "date": target_date,
            "created": created,
            "updated": updated,
        }
