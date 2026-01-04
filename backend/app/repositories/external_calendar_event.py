"""Repository for external calendar events."""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, func
from app.models.external_calendar_event import ExternalCalendarEvent


class ExternalCalendarEventRepository:
    """Data access for imported calendar events."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def replace_events(
        self,
        user_id: int,
        provider: str,
        source: str,
        events: list[dict],
    ) -> int:
        await self.session.execute(
            delete(ExternalCalendarEvent).where(
                ExternalCalendarEvent.user_id == user_id,
                ExternalCalendarEvent.provider == provider,
                ExternalCalendarEvent.source == source,
            )
        )
        if events:
            self.session.add_all([ExternalCalendarEvent(**event) for event in events])
        await self.session.commit()
        return len(events)

    async def list_events(
        self,
        user_id: int,
        provider: str,
        source: str,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[ExternalCalendarEvent]:
        query = select(ExternalCalendarEvent).where(
            ExternalCalendarEvent.user_id == user_id,
            ExternalCalendarEvent.provider == provider,
            ExternalCalendarEvent.source == source,
        )
        if start is not None:
            query = query.where(ExternalCalendarEvent.starts_at >= start)
        if end is not None:
            query = query.where(ExternalCalendarEvent.starts_at <= end)
        query = query.order_by(ExternalCalendarEvent.starts_at)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_status(
        self, user_id: int, provider: str, source: str
    ) -> tuple[int, datetime | None, str | None]:
        result = await self.session.execute(
            select(
                func.count(ExternalCalendarEvent.id),
                func.max(ExternalCalendarEvent.updated_at),
                func.max(ExternalCalendarEvent.calendar_name),
            ).where(
                ExternalCalendarEvent.user_id == user_id,
                ExternalCalendarEvent.provider == provider,
                ExternalCalendarEvent.source == source,
            )
        )
        count, last_updated, calendar_name = result.one()
        return int(count or 0), last_updated, calendar_name

    async def clear_events(self, user_id: int, provider: str, source: str) -> None:
        await self.session.execute(
            delete(ExternalCalendarEvent).where(
                ExternalCalendarEvent.user_id == user_id,
                ExternalCalendarEvent.provider == provider,
                ExternalCalendarEvent.source == source,
            )
        )
        await self.session.commit()
