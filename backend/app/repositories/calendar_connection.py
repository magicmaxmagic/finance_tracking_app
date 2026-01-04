"""Repository for calendar connections."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.calendar_connection import CalendarConnection


class CalendarConnectionRepository:
    """Data access for calendar connections."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_provider(self, user_id: int, provider: str) -> CalendarConnection | None:
        result = await self.session.execute(
            select(CalendarConnection).where(
                CalendarConnection.user_id == user_id,
                CalendarConnection.provider == provider,
            )
        )
        return result.scalar_one_or_none()

    async def upsert(self, user_id: int, provider: str, **kwargs) -> CalendarConnection:
        connection = await self.get_by_user_provider(user_id, provider)
        if connection:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(connection, key, value)
            self.session.add(connection)
            await self.session.commit()
            await self.session.refresh(connection)
            return connection

        connection = CalendarConnection(user_id=user_id, provider=provider, **kwargs)
        self.session.add(connection)
        await self.session.commit()
        await self.session.refresh(connection)
        return connection

    async def update(self, connection: CalendarConnection, **kwargs) -> CalendarConnection:
        for key, value in kwargs.items():
            if value is not None:
                setattr(connection, key, value)
        self.session.add(connection)
        await self.session.commit()
        await self.session.refresh(connection)
        return connection

    async def delete(self, connection: CalendarConnection) -> None:
        await self.session.delete(connection)
        await self.session.commit()
