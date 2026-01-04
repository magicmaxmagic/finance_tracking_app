"""Repository for user subscriptions."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.subscription import UserSubscription


class SubscriptionRepository:
    """User subscription repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user(self, user_id: int) -> UserSubscription | None:
        result = await self.session.execute(
            select(UserSubscription).where(UserSubscription.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_customer_id(self, customer_id: str) -> UserSubscription | None:
        result = await self.session.execute(
            select(UserSubscription).where(UserSubscription.stripe_customer_id == customer_id)
        )
        return result.scalar_one_or_none()

    async def get_by_subscription_id(self, subscription_id: str) -> UserSubscription | None:
        result = await self.session.execute(
            select(UserSubscription).where(UserSubscription.stripe_subscription_id == subscription_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: int, **kwargs) -> UserSubscription:
        subscription = UserSubscription(user_id=user_id, **kwargs)
        self.session.add(subscription)
        await self.session.commit()
        await self.session.refresh(subscription)
        return subscription

    async def update(self, subscription: UserSubscription, **kwargs) -> UserSubscription:
        for key, value in kwargs.items():
            if value is not None:
                setattr(subscription, key, value)
        self.session.add(subscription)
        await self.session.commit()
        await self.session.refresh(subscription)
        return subscription
