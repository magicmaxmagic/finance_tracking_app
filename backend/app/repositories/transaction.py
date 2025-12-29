"""Transaction repository for database operations."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from datetime import datetime, date
from app.models.transaction import Transaction


class TransactionRepository:
    """Repository for transaction operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, transaction_id: int, user_id: int) -> Transaction | None:
        """Get transaction by ID (ensure user ownership)."""
        result = await self.session.execute(
            select(Transaction).where(
                Transaction.id == transaction_id,
                Transaction.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_all_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        category_id: int | None = None,
        account_id: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        search: str | None = None,
    ) -> tuple[list[Transaction], int]:
        """Get paginated transactions with filters."""
        query = select(Transaction).where(Transaction.user_id == user_id)
        
        if category_id:
            query = query.where(Transaction.category_id == category_id)
        if account_id:
            query = query.where(Transaction.account_id == account_id)
        if start_date:
            query = query.where(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.where(Transaction.transaction_date <= end_date)
        if search:
            query = query.where(
                or_(
                    Transaction.description.ilike(f"%{search}%"),
                    Transaction.notes.ilike(f"%{search}%"),
                    Transaction.tags.ilike(f"%{search}%"),
                )
            )
        
        # Count total
        count_query = select(Transaction).where(Transaction.user_id == user_id)
        
        if category_id:
            count_query = count_query.where(Transaction.category_id == category_id)
        if account_id:
            count_query = count_query.where(Transaction.account_id == account_id)
        if start_date:
            count_query = count_query.where(Transaction.transaction_date >= start_date)
        if end_date:
            count_query = count_query.where(Transaction.transaction_date <= end_date)
        if search:
            count_query = count_query.where(
                or_(
                    Transaction.description.ilike(f"%{search}%"),
                    Transaction.notes.ilike(f"%{search}%"),
                    Transaction.tags.ilike(f"%{search}%"),
                )
            )
        
        from sqlalchemy import func
        count_result = await self.session.execute(
            count_query.with_only_columns(func.count(Transaction.id)).order_by(None)
        )
        total = int(count_result.scalar() or 0)
        
        # Get paginated results
        query = query.order_by(desc(Transaction.transaction_date)).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all()), total
    
    async def create(self, user_id: int, **kwargs) -> Transaction:
        """Create a new transaction."""
        transaction = Transaction(user_id=user_id, **kwargs)
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction
    
    async def update(self, transaction_id: int, user_id: int, **kwargs) -> Transaction | None:
        """Update transaction."""
        transaction = await self.get_by_id(transaction_id, user_id)
        if not transaction:
            return None
        
        for key, value in kwargs.items():
            if value is not None:
                setattr(transaction, key, value)
        
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction
    
    async def delete(self, transaction_id: int, user_id: int) -> bool:
        """Delete transaction."""
        transaction = await self.get_by_id(transaction_id, user_id)
        if not transaction:
            return False
        
        await self.session.delete(transaction)
        await self.session.commit()
        return True
    
    async def get_by_import_id(self, import_id: str, user_id: int) -> Transaction | None:
        """Get transaction by import ID for deduplication."""
        result = await self.session.execute(
            select(Transaction).where(
                Transaction.import_id == import_id,
                Transaction.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_monthly_total(self, user_id: int, year: int, month: int) -> float:
        """Get total expenses for a month."""
        from sqlalchemy import extract, func
        
        result = await self.session.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.user_id == user_id,
                extract('year', Transaction.transaction_date) == year,
                extract('month', Transaction.transaction_date) == month,
                Transaction.amount < 0,  # Only expenses (negative amounts)
            )
        )
        total = result.scalar() or 0
        return abs(float(total))
