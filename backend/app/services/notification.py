"""Notification service."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.notification import NotificationRepository
from app.schemas.notification import NotificationResponse


class NotificationService:
    """Service for notifications."""

    def __init__(self, session: AsyncSession):
        self.repository = NotificationRepository(session)
        self.session = session

    async def get_notifications(self, user_id: int) -> list[NotificationResponse]:
        notifications = await self.repository.get_all_by_user(user_id)
        return [NotificationResponse.from_orm(n) for n in notifications]

    async def create_notification(self, user_id: int, title: str, message: str,
                                  notification_type: str = "info") -> NotificationResponse:
        notification = await self.repository.create(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
        )
        return NotificationResponse.from_orm(notification)

    async def mark_read(self, notification_id: int, user_id: int) -> NotificationResponse:
        notification = await self.repository.mark_read(notification_id, user_id)
        if not notification:
            raise ValueError("Notification not found")
        return NotificationResponse.from_orm(notification)
