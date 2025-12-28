"""Account repository for database operations."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.account import Account


class AccountRepository:
    """Repository for account operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, account_id: int, user_id: int) -> Account | None:
        """Get account by ID (ensure user ownership)."""
        result = await self.session.execute(
            select(Account).where(
                Account.id == account_id,
                Account.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_all_by_user(self, user_id: int) -> list[Account]:
        """Get all accounts for user."""
        result = await self.session.execute(
            select(Account).where(Account.user_id == user_id).order_by(Account.created_at)
        )
        return list(result.scalars().all())
    
    async def create(self, user_id: int, **kwargs) -> Account:
        """Create a new account."""
        account = Account(user_id=user_id, **kwargs)
        self.session.add(account)
        await self.session.commit()
        await self.session.refresh(account)
        return account
    
    async def update(self, account_id: int, user_id: int, **kwargs) -> Account | None:
        """Update account."""
        account = await self.get_by_id(account_id, user_id)
        if not account:
            return None
        
        for key, value in kwargs.items():
            if value is not None:
                setattr(account, key, value)
        
        self.session.add(account)
        await self.session.commit()
        await self.session.refresh(account)
        return account
    
    async def delete(self, account_id: int, user_id: int) -> bool:
        """Delete account."""
        account = await self.get_by_id(account_id, user_id)
        if not account:
            return False
        
        await self.session.delete(account)
        await self.session.commit()
        return True
