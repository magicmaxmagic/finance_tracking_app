"""Repository for user settings."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user_settings import UserSettings


class SettingsRepository:
    """User settings repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user(self, user_id: int) -> UserSettings | None:
        result = await self.session.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: int, **kwargs) -> UserSettings:
        settings = UserSettings(user_id=user_id, **kwargs)
        self.session.add(settings)
        await self.session.commit()
        await self.session.refresh(settings)
        return settings

    async def get_by_calendar_feed_token(self, token: str) -> UserSettings | None:
        result = await self.session.execute(
            select(UserSettings).where(UserSettings.calendar_feed_token == token)
        )
        return result.scalar_one_or_none()

    async def update(self, settings: UserSettings, **kwargs) -> UserSettings:
        for key, value in kwargs.items():
            if value is not None:
                setattr(settings, key, value)
        self.session.add(settings)
        await self.session.commit()
        await self.session.refresh(settings)
        return settings
