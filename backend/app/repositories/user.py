"""User repository for database operations."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User


class UserRepository:
    """Repository for user operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""
        return await self.session.get(User, user_id)
    
    async def create(self, email: str, hashed_password: str, full_name: str | None = None) -> User:
        """Create a new user."""
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def update(self, user_id: int, **kwargs) -> User | None:
        """Update user."""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        for key, value in kwargs.items():
            if value is not None:
                setattr(user, key, value)
        
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
