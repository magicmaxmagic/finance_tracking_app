"""Service for importing calendar files."""
from datetime import datetime, date
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.external_calendar_event import ExternalCalendarEventRepository
from app.schemas.calendar import (
    CalendarEventResponse,
    CalendarImportStatus,
    CalendarProvider,
)
from app.services.caldav import CalDAVClient
from app.services.settings import SettingsService


class CalendarImportService:
    """Import calendar events from ICS files."""

    SOURCE_ICS = "ics"

    def __init__(self, session: AsyncSession):
        self.repository = ExternalCalendarEventRepository(session)
        self.settings_service = SettingsService(session)

    async def import_ics(self, user_id: int, provider: CalendarProvider, ics_text: str) -> CalendarImportStatus:
        calendar_name, calendar_tz = self._extract_metadata(ics_text)
        if calendar_name:
            calendar_name = calendar_name[:255]
        if calendar_tz:
            calendar_tz = calendar_tz[:64]
        settings = await self.settings_service.get_settings(user_id)
        fallback_tz = calendar_tz or (settings.timezone if settings else None)

        events = CalDAVClient.parse_ics_events(ics_text, fallback_tz=fallback_tz)
        if not events:
            raise ValueError("No events found in the file")

        payloads: list[dict] = []
        for event in events:
            start_dt = self._normalize_datetime(event.start, fallback_tz)
            end_dt = self._normalize_datetime(event.end, fallback_tz)
            summary = event.summary[:255] if event.summary else None
            payloads.append(
                {
                    "user_id": user_id,
                    "provider": provider.value,
                    "source": self.SOURCE_ICS,
                    "calendar_name": calendar_name,
                    "timezone": fallback_tz,
                    "summary": summary,
                    "starts_at": start_dt,
                    "ends_at": end_dt,
                    "is_all_day": event.is_all_day,
                }
            )

        imported = await self.repository.replace_events(user_id, provider.value, self.SOURCE_ICS, payloads)
        return CalendarImportStatus(
            provider=provider,
            source=self.SOURCE_ICS,
            calendar_name=calendar_name,
            event_count=imported,
            last_imported_at=datetime.utcnow(),
        )

    async def get_status(self, user_id: int, provider: CalendarProvider) -> CalendarImportStatus:
        count, last_updated, calendar_name = await self.repository.get_status(
            user_id, provider.value, self.SOURCE_ICS
        )
        return CalendarImportStatus(
            provider=provider,
            source=self.SOURCE_ICS,
            calendar_name=calendar_name,
            event_count=count,
            last_imported_at=last_updated,
        )

    async def list_events(
        self,
        user_id: int,
        provider: CalendarProvider,
        include_details: bool = False,
        start: date | None = None,
        end: date | None = None,
    ) -> list[CalendarEventResponse]:
        start_dt = datetime.combine(start, datetime.min.time()) if start else None
        end_dt = datetime.combine(end, datetime.min.time()) if end else None
        events = await self.repository.list_events(
            user_id, provider.value, self.SOURCE_ICS, start=start_dt, end=end_dt
        )
        response: list[CalendarEventResponse] = []
        for event in events:
            summary = event.summary if include_details else "Busy"
            response.append(
                CalendarEventResponse(
                    start=event.starts_at,
                    end=event.ends_at,
                    summary=summary,
                    is_all_day=event.is_all_day,
                )
            )
        return response

    async def clear_events(self, user_id: int, provider: CalendarProvider) -> None:
        await self.repository.clear_events(user_id, provider.value, self.SOURCE_ICS)

    def _extract_metadata(self, ics_text: str) -> tuple[str | None, str | None]:
        calendar_name = None
        calendar_tz = None
        for line in ics_text.replace("\r\n", "\n").split("\n"):
            if line.startswith("X-WR-CALNAME:"):
                calendar_name = line.split(":", 1)[1].strip()
            elif line.startswith("X-WR-TIMEZONE:"):
                calendar_tz = line.split(":", 1)[1].strip()
        return calendar_name, calendar_tz

    def _normalize_datetime(self, value, tz_name: str | None) -> datetime:
        if isinstance(value, date) and not isinstance(value, datetime):
            dt = datetime.combine(value, datetime.min.time())
        else:
            dt = value

        if isinstance(dt, datetime) and dt.tzinfo:
            tz = self._resolve_timezone(tz_name) if tz_name else dt.tzinfo
            dt = dt.astimezone(tz).replace(tzinfo=None)
        return dt

    def _resolve_timezone(self, tz_name: str | None):
        if not tz_name:
            return ZoneInfo("UTC")
        try:
            return ZoneInfo(tz_name)
        except ZoneInfoNotFoundError:
            return ZoneInfo("UTC")
