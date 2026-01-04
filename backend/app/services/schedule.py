"""Schedule service for weekly planning and calendar export."""
from datetime import datetime, timedelta, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.schedule import ScheduleRepository
from app.schemas.schedule import ScheduleBlockCreate, ScheduleBlockUpdate, ScheduleBlockResponse
from app.services.settings import SettingsService


WEEKDAY_CODES = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]

DEFAULT_BLOCKS: list[dict] = [
    {
        "title": "Weekly finance plan",
        "description": "Set weekly money goals and pick 1-3 priorities.",
        "category": "FINANCE",
        "day_of_week": 0,
        "start_time": time(8, 30),
        "duration_minutes": 30,
        "is_active": True,
    },
    {
        "title": "Build value block",
        "description": "Deep work on income-generating project.",
        "category": "REVENUE",
        "day_of_week": 0,
        "start_time": time(19, 0),
        "duration_minutes": 120,
        "is_active": True,
    },
    {
        "title": "Income outreach",
        "description": "Outreach, sales, leads, or client follow-up.",
        "category": "REVENUE",
        "day_of_week": 1,
        "start_time": time(18, 30),
        "duration_minutes": 60,
        "is_active": True,
    },
    {
        "title": "Build value block",
        "description": "Deep work on income-generating project.",
        "category": "REVENUE",
        "day_of_week": 2,
        "start_time": time(19, 0),
        "duration_minutes": 120,
        "is_active": True,
    },
    {
        "title": "Income outreach",
        "description": "Outreach, sales, leads, or client follow-up.",
        "category": "REVENUE",
        "day_of_week": 3,
        "start_time": time(18, 30),
        "duration_minutes": 60,
        "is_active": True,
    },
    {
        "title": "Finance admin",
        "description": "Budget, expenses, invoices, and tracking.",
        "category": "FINANCE",
        "day_of_week": 4,
        "start_time": time(12, 0),
        "duration_minutes": 45,
        "is_active": True,
    },
    {
        "title": "Skill building",
        "description": "Learning that increases earning potential.",
        "category": "SKILL",
        "day_of_week": 5,
        "start_time": time(10, 0),
        "duration_minutes": 60,
        "is_active": True,
    },
    {
        "title": "Weekly review",
        "description": "Review results and adjust next week.",
        "category": "FINANCE",
        "day_of_week": 6,
        "start_time": time(17, 30),
        "duration_minutes": 30,
        "is_active": True,
    },
]


class ScheduleService:
    """Service for schedule block operations."""

    def __init__(self, session: AsyncSession):
        self.repository = ScheduleRepository(session)
        self.settings_service = SettingsService(session)

    async def get_blocks(self, user_id: int) -> list[ScheduleBlockResponse]:
        """Get all blocks, seeding defaults if needed."""
        blocks = await self.repository.get_all_by_user(user_id)
        if not blocks:
            blocks = await self.repository.create_bulk(user_id, DEFAULT_BLOCKS)
        return [ScheduleBlockResponse.from_orm(block) for block in blocks]

    async def create_block(self, user_id: int, payload: ScheduleBlockCreate) -> ScheduleBlockResponse:
        """Create a new schedule block."""
        block = await self.repository.create(user_id=user_id, **payload.dict())
        return ScheduleBlockResponse.from_orm(block)

    async def update_block(
        self, block_id: int, user_id: int, payload: ScheduleBlockUpdate
    ) -> ScheduleBlockResponse:
        """Update a schedule block."""
        update_data = payload.dict(exclude_unset=True)
        block = await self.repository.update(block_id, user_id, **update_data)
        if not block:
            raise ValueError("Schedule block not found")
        return ScheduleBlockResponse.from_orm(block)

    async def delete_block(self, block_id: int, user_id: int) -> bool:
        """Delete a schedule block."""
        success = await self.repository.delete(block_id, user_id)
        if not success:
            raise ValueError("Schedule block not found")
        return success

    async def export_ics(self, user_id: int, timezone_override: str | None = None) -> str:
        """Generate ICS calendar feed for user's schedule blocks."""
        blocks = await self.repository.get_all_by_user(user_id)
        if not blocks:
            blocks = await self.repository.create_bulk(user_id, DEFAULT_BLOCKS)

        settings = await self.settings_service.get_settings(user_id)
        tz_name = timezone_override or settings.timezone or "UTC"
        tz = self._resolve_timezone(tz_name)
        return self._build_ics(blocks, tz_name, tz)

    async def export_ics_by_token(self, token: str, timezone_override: str | None = None) -> str | None:
        """Generate ICS calendar feed using a public calendar token."""
        settings = await self.settings_service.get_settings_by_calendar_token(token)
        if not settings:
            return None
        return await self.export_ics(settings.user_id, timezone_override=timezone_override)

    def _resolve_timezone(self, tz_name: str) -> ZoneInfo:
        try:
            return ZoneInfo(tz_name)
        except ZoneInfoNotFoundError:
            return ZoneInfo("UTC")

    def _next_occurrence(self, day_of_week: int, start: time, tz: ZoneInfo) -> datetime:
        now = datetime.now(tz)
        days_ahead = (day_of_week - now.weekday()) % 7
        candidate_date = (now + timedelta(days=days_ahead)).date()
        candidate = datetime.combine(candidate_date, start, tzinfo=tz)
        if candidate <= now:
            candidate += timedelta(days=7)
        return candidate

    def _escape_ics_text(self, value: str) -> str:
        return (
            value.replace("\\", "\\\\")
            .replace(";", "\\;")
            .replace(",", "\\,")
            .replace("\n", "\\n")
        )

    def _build_ics(self, blocks, tz_name: str, tz: ZoneInfo) -> str:
        now_utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//finance-tracker//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Finance Schedule",
            f"X-WR-TIMEZONE:{tz_name}",
        ]

        for block in blocks:
            if not block.is_active:
                continue

            start = self._next_occurrence(block.day_of_week, block.start_time, tz)
            end = start + timedelta(minutes=block.duration_minutes)
            weekday_code = WEEKDAY_CODES[block.day_of_week]
            uid = f"schedule-block-{block.id}@finance-tracker"

            lines.extend(
                [
                    "BEGIN:VEVENT",
                    f"UID:{uid}",
                    f"DTSTAMP:{now_utc}",
                    f"DTSTART;TZID={tz_name}:{start.strftime('%Y%m%dT%H%M%S')}",
                    f"DTEND;TZID={tz_name}:{end.strftime('%Y%m%dT%H%M%S')}",
                    f"SUMMARY:{self._escape_ics_text(block.title)}",
                    f"DESCRIPTION:{self._escape_ics_text(block.description or '')}",
                    f"CATEGORIES:{self._escape_ics_text(block.category)}",
                    f"RRULE:FREQ=WEEKLY;BYDAY={weekday_code}",
                    "TRANSP:OPAQUE",
                    "END:VEVENT",
                ]
            )

        lines.append("END:VCALENDAR")
        return "\r\n".join(lines) + "\r\n"
