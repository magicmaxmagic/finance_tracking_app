"""Investment asset repository for database operations."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.investment import InvestmentAsset


class InvestmentRepository:
    """Repository for investment asset operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, investment_id: int, user_id: int) -> InvestmentAsset | None:
        """Get investment asset by ID (ensure user ownership)."""
        result = await self.session.execute(
            select(InvestmentAsset).where(
                InvestmentAsset.id == investment_id,
                InvestmentAsset.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_by_user(self, user_id: int) -> list[InvestmentAsset]:
        """Get all investment assets for user."""
        result = await self.session.execute(
            select(InvestmentAsset)
            .where(InvestmentAsset.user_id == user_id)
            .order_by(InvestmentAsset.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, user_id: int, **kwargs) -> InvestmentAsset:
        """Create a new investment asset."""
        investment = InvestmentAsset(user_id=user_id, **kwargs)
        self.session.add(investment)
        await self.session.commit()
        await self.session.refresh(investment)
        return investment

    async def update(
        self, investment_id: int, user_id: int, **kwargs
    ) -> InvestmentAsset | None:
        """Update investment asset."""
        investment = await self.get_by_id(investment_id, user_id)
        if not investment:
            return None

        for key, value in kwargs.items():
            if value is not None:
                setattr(investment, key, value)

        self.session.add(investment)
        await self.session.commit()
        await self.session.refresh(investment)
        return investment

    async def delete(self, investment_id: int, user_id: int) -> bool:
        """Delete investment asset."""
        investment = await self.get_by_id(investment_id, user_id)
        if not investment:
            return False

        await self.session.delete(investment)
        await self.session.commit()
        return True
