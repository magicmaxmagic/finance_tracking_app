"""Net worth service for net worth calculations."""
from decimal import Decimal
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.repositories.net_worth import NetWorthSnapshotRepository
from app.models.account import Account, AccountType
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
        
        total_assets = Decimal("0")
        total_liabilities = Decimal("0")
        breakdown = {}
        
        for account in accounts:
            balance = account.balance
            account_type = account.account_type
            
            # Categorize as asset or liability
            if account_type in [AccountType.DEBT, AccountType.CREDIT]:
                total_liabilities += abs(balance) if balance < 0 else balance
            else:
                total_assets += balance
            
            # Build breakdown
            type_key = account_type.value
            if type_key not in breakdown:
                breakdown[type_key] = Decimal("0")
            breakdown[type_key] += balance
        
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
