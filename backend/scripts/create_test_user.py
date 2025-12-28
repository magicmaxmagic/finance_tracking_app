"""Create main script for utilities"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.user import User
from app.core.security import hash_password
from app.core.config import settings


async def create_test_user():
    """Create a test user for development."""
    engine = create_async_engine(settings.DATABASE_URL)
    
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        # Check if user exists
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.email == "test@example.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                email="test@example.com",
                hashed_password=hash_password("password123"),
                full_name="Test User",
            )
            session.add(user)
            await session.commit()
            print("Test user created: test@example.com / password123")
        else:
            print("Test user already exists")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_test_user())
