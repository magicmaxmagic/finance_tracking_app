"""Service for external calendar connections."""
from datetime import datetime, date, timedelta
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.crypto import encrypt_string, decrypt_string
from app.repositories.calendar_connection import CalendarConnectionRepository
from app.schemas.calendar import (
    AppleCalendarConnectRequest,
    CalendarConnectionResponse,
    CalendarEventResponse,
    CalendarInfoResponse,
    CalendarProvider,
)
from app.services.caldav import CalDAVClient
from app.services.settings import SettingsService


class CalendarConnectionService:
    """Service layer for external calendar integrations."""

    def __init__(self, session: AsyncSession):
        self.repository = CalendarConnectionRepository(session)
        self.settings_service = SettingsService(session)

    async def get_connection(self, user_id: int, provider: CalendarProvider) -> CalendarConnectionResponse | None:
        connection = await self.repository.get_by_user_provider(user_id, provider.value)
        if not connection:
            return None
        return CalendarConnectionResponse.model_validate(connection, from_attributes=True)

    async def connect_apple(
        self, user_id: int, payload: AppleCalendarConnectRequest
    ) -> CalendarConnectionResponse:
        client = CalDAVClient(payload.email, payload.app_password)
        try:
            calendars = await client.list_calendars()
        except httpx.HTTPError as exc:
            raise ValueError("Unable to reach Apple Calendar. Check credentials or network.") from exc
        if not calendars:
            raise ValueError("No calendars found for this account")

        selected = self._select_calendar(calendars, payload.calendar_name)
        if not selected:
            raise ValueError("Calendar not found")

        encrypted_secret = encrypt_string(payload.app_password)
        connection = await self.repository.upsert(
            user_id=user_id,
            provider=CalendarProvider.APPLE.value,
            account_email=payload.email,
            calendar_name=selected.name,
            calendar_url=selected.url,
            encrypted_secret=encrypted_secret,
            is_active=True,
        )
        return CalendarConnectionResponse.model_validate(connection, from_attributes=True)

    async def disconnect(self, user_id: int, provider: CalendarProvider) -> None:
        connection = await self.repository.get_by_user_provider(user_id, provider.value)
        if not connection:
            return
        await self.repository.delete(connection)

    async def list_apple_calendars(self, user_id: int) -> list[CalendarInfoResponse]:
        connection = await self.repository.get_by_user_provider(user_id, CalendarProvider.APPLE.value)
        if not connection:
            raise ValueError("Apple Calendar not connected")
        secret = decrypt_string(connection.encrypted_secret)
        client = CalDAVClient(connection.account_email, secret)
        try:
            calendars = await client.list_calendars()
        except httpx.HTTPError as exc:
            raise ValueError("Unable to reach Apple Calendar. Check credentials or network.") from exc
        return [CalendarInfoResponse(name=item.name, url=item.url) for item in calendars]

    async def get_apple_events(
        self,
        user_id: int,
        start: date | None = None,
        end: date | None = None,
        include_details: bool = False,
    ) -> list[CalendarEventResponse]:
        connection = await self.repository.get_by_user_provider(user_id, CalendarProvider.APPLE.value)
        if not connection:
            raise ValueError("Apple Calendar not connected")

        secret = decrypt_string(connection.encrypted_secret)
        client = CalDAVClient(connection.account_email, secret)

        if not connection.calendar_url:
            calendars = await client.list_calendars()
            if not calendars:
                raise ValueError("No calendars found for this account")
            connection = await self.repository.update(connection, calendar_url=calendars[0].url)

        settings = await self.settings_service.get_settings(user_id)
        timezone_name = settings.timezone if settings else None
        start_dt = datetime.combine(start or date.today(), datetime.min.time())
        end_dt = datetime.combine(end or (date.today() + timedelta(days=30)), datetime.min.time())

        try:
            events = await client.fetch_events(connection.calendar_url, start_dt, end_dt, fallback_tz=timezone_name)
        except httpx.HTTPError as exc:
            raise ValueError("Unable to reach Apple Calendar. Check credentials or network.") from exc
        await self.repository.update(connection, last_sync_at=datetime.utcnow())

        response: list[CalendarEventResponse] = []
        for event in events:
            summary = event.summary if include_details else "Busy"
            response.append(
                CalendarEventResponse(
                    start=event.start,
                    end=event.end,
                    summary=summary,
                    is_all_day=event.is_all_day,
                )
            )
        return response

    def _select_calendar(self, calendars, calendar_name: str | None):
        if not calendar_name:
            return calendars[0] if calendars else None
        normalized = calendar_name.strip().lower()
        for calendar in calendars:
            if calendar.name.strip().lower() == normalized:
                return calendar
        return None
