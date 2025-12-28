"""Account service for account-related business logic."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.account import AccountRepository
from app.schemas.account import AccountResponse


class AccountService:
    """Service for account operations."""
    
    def __init__(self, session: AsyncSession):
        self.repository = AccountRepository(session)
        self.session = session
    
    async def get_account(self, account_id: int, user_id: int) -> AccountResponse:
        """Get account by ID."""
        account = await self.repository.get_by_id(account_id, user_id)
        if not account:
            raise ValueError("Account not found")
        return AccountResponse.from_orm(account)
    
    async def get_all_accounts(self, user_id: int) -> list[AccountResponse]:
        """Get all accounts for user."""
        accounts = await self.repository.get_all_by_user(user_id)
        return [AccountResponse.from_orm(acc) for acc in accounts]
    
    async def create_account(self, user_id: int, **kwargs) -> AccountResponse:
        """Create a new account."""
        account = await self.repository.create(user_id=user_id, **kwargs)
        return AccountResponse.from_orm(account)
    
    async def update_account(self, account_id: int, user_id: int, **kwargs) -> AccountResponse:
        """Update account."""
        account = await self.repository.update(account_id, user_id, **kwargs)
        if not account:
            raise ValueError("Account not found")
        return AccountResponse.from_orm(account)
    
    async def delete_account(self, account_id: int, user_id: int) -> bool:
        """Delete account."""
        success = await self.repository.delete(account_id, user_id)
        if not success:
            raise ValueError("Account not found")
        return success
