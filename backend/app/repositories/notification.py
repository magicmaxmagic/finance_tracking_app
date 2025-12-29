"""Notification repository."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.notification import Notification


class NotificationRepository:
    """Repository for notifications."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_by_user(self, user_id: int) -> list[Notification]:
        result = await self.session.execute(
            select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, user_id: int, **kwargs) -> Notification:
        notification = Notification(user_id=user_id, **kwargs)
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification

    async def mark_read(self, notification_id: int, user_id: int) -> Notification | None:
        result = await self.session.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notification = result.scalar_one_or_none()
        if not notification:
            return None
        notification.is_read = True
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification
