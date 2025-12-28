"""Script - Initialize database with seed data"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from datetime import datetime, date, timedelta
from decimal import Decimal
from app.models.user import User
from app.models.account import Account, AccountType
from app.models.category import Category
from app.models.budget import Budget
from app.core.security import hash_password
from app.core.config import settings


async def seed_database():
    """Seed database with test data."""
    engine = create_async_engine(settings.DATABASE_URL)
    
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        # Create test user
        user = User(
            email="demo@example.com",
            hashed_password=hash_password("demo123"),
            full_name="Demo User",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        print(f"✅ Created user: {user.email}")
        
        # Create accounts
        accounts = [
            Account(
                user_id=user.id,
                name="Checking Account",
                account_type=AccountType.CHECKING,
                balance=Decimal("5000.00"),
                description="Main bank account",
            ),
            Account(
                user_id=user.id,
                name="Savings Account",
                account_type=AccountType.SAVINGS,
                balance=Decimal("10000.00"),
                description="Emergency fund",
            ),
            Account(
                user_id=user.id,
                name="Credit Card",
                account_type=AccountType.CREDIT,
                balance=Decimal("-2500.00"),
                description="Primary credit card",
            ),
        ]
        
        for account in accounts:
            session.add(account)
        
        await session.commit()
        print(f"✅ Created {len(accounts)} accounts")
        
        # Create categories
        categories = [
            Category(
                user_id=user.id,
                name="Food & Groceries",
                color="#FF6B6B",
                icon="🍔",
                is_income=False,
            ),
            Category(
                user_id=user.id,
                name="Transportation",
                color="#4ECDC4",
                icon="🚗",
                is_income=False,
            ),
            Category(
                user_id=user.id,
                name="Entertainment",
                color="#FFE66D",
                icon="🎬",
                is_income=False,
            ),
            Category(
                user_id=user.id,
                name="Salary",
                color="#95E1D3",
                icon="💰",
                is_income=True,
            ),
        ]
        
        for category in categories:
            session.add(category)
        
        await session.commit()
        print(f"✅ Created {len(categories)} categories")
        
        # Create budgets
        today = date.today()
        first_of_month = date(today.year, today.month, 1)
        
        budgets = [
            Budget(
                user_id=user.id,
                category_id=categories[0].id,  # Food
                amount=Decimal("500.00"),
                month=first_of_month,
            ),
            Budget(
                user_id=user.id,
                category_id=categories[1].id,  # Transportation
                amount=Decimal("300.00"),
                month=first_of_month,
            ),
        ]
        
        for budget in budgets:
            session.add(budget)
        
        await session.commit()
        print(f"✅ Created {len(budgets)} budgets")
        
        print("\n✅ Seeding complete!")
        print(f"\nTest account:")
        print(f"  Email: demo@example.com")
        print(f"  Password: demo123")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())
