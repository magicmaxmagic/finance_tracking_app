"""Net worth snapshot repository for database operations."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import date
from app.models.net_worth_snapshot import NetWorthSnapshot


class NetWorthSnapshotRepository:
    """Repository for net worth snapshot operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, snapshot_id: int, user_id: int) -> NetWorthSnapshot | None:
        """Get snapshot by ID (ensure user ownership)."""
        result = await self.session.execute(
            select(NetWorthSnapshot).where(
                NetWorthSnapshot.id == snapshot_id,
                NetWorthSnapshot.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_all_by_user(self, user_id: int) -> list[NetWorthSnapshot]:
        """Get all snapshots for user."""
        result = await self.session.execute(
            select(NetWorthSnapshot)
            .where(NetWorthSnapshot.user_id == user_id)
            .order_by(NetWorthSnapshot.snapshot_date.desc())
        )
        return list(result.scalars().all())
    
    async def get_latest_by_account(self, account_id: int, user_id: int) -> NetWorthSnapshot | None:
        """Get latest snapshot for an account."""
        result = await self.session.execute(
            select(NetWorthSnapshot)
            .where(
                NetWorthSnapshot.account_id == account_id,
                NetWorthSnapshot.user_id == user_id
            )
            .order_by(NetWorthSnapshot.snapshot_date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_by_date_range(
        self, user_id: int, start_date: date, end_date: date
    ) -> list[NetWorthSnapshot]:
        """Get snapshots in a date range."""
        result = await self.session.execute(
            select(NetWorthSnapshot)
            .where(
                NetWorthSnapshot.user_id == user_id,
                NetWorthSnapshot.snapshot_date >= start_date,
                NetWorthSnapshot.snapshot_date <= end_date
            )
            .order_by(NetWorthSnapshot.snapshot_date)
        )
        return list(result.scalars().all())
    
    async def create(self, user_id: int, **kwargs) -> NetWorthSnapshot:
        """Create a new snapshot."""
        snapshot = NetWorthSnapshot(user_id=user_id, **kwargs)
        self.session.add(snapshot)
        await self.session.commit()
        await self.session.refresh(snapshot)
        return snapshot
    
    async def delete(self, snapshot_id: int, user_id: int) -> bool:
        """Delete snapshot."""
        snapshot = await self.get_by_id(snapshot_id, user_id)
        if not snapshot:
            return False
        
        await self.session.delete(snapshot)
        await self.session.commit()
        return True
