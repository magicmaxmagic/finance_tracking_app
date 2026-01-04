"""Minimal CalDAV client for read-only calendar access."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date, timedelta, timezone
from urllib.parse import urljoin
from xml.etree import ElementTree
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import httpx


NS = {
    "d": "DAV:",
    "c": "urn:ietf:params:xml:ns:caldav",
}


@dataclass
class CalendarInfo:
    name: str
    url: str


@dataclass
class CalendarEvent:
    start: datetime | date
    end: datetime | date
    summary: str | None
    is_all_day: bool


class CalDAVClient:
    """Lightweight CalDAV client for fetching calendar events."""

    def __init__(self, email: str, app_password: str, base_url: str = "https://caldav.icloud.com"):
        self.email = email
        self.app_password = app_password
        self.base_url = base_url.rstrip("/") + "/"

    @staticmethod
    def parse_ics_events(ics_text: str, fallback_tz: str | None = None) -> list["CalendarEvent"]:
        parser = CalDAVClient("", "")
        return parser._parse_ics(ics_text, fallback_tz)

    async def list_calendars(self) -> list[CalendarInfo]:
        principal_url = await self._discover_principal_url()
        calendar_home = await self._discover_calendar_home(principal_url)
        return await self._fetch_calendars(calendar_home)

    async def fetch_events(
        self,
        calendar_url: str,
        start: datetime,
        end: datetime,
        fallback_tz: str | None = None,
    ) -> list[CalendarEvent]:
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        start_utc = start.astimezone(timezone.utc)
        end_utc = end.astimezone(timezone.utc)

        body = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<c:calendar-query xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">'
            "<d:prop><c:calendar-data/></d:prop>"
            "<c:filter>"
            '<c:comp-filter name="VCALENDAR">'
            '<c:comp-filter name="VEVENT">'
            f'<c:time-range start="{start_utc.strftime("%Y%m%dT%H%M%SZ")}" '
            f'end="{end_utc.strftime("%Y%m%dT%H%M%SZ")}"/>'
            "</c:comp-filter>"
            "</c:comp-filter>"
            "</c:filter>"
            "</c:calendar-query>"
        )

        text = await self._request("REPORT", calendar_url, body=body)
        events: list[CalendarEvent] = []
        for calendar_data in self._iter_calendar_data(text):
            events.extend(self._parse_ics(calendar_data, fallback_tz))
        return events

    async def _discover_principal_url(self) -> str:
        body = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<d:propfind xmlns:d="DAV:"><d:prop>'
            "<d:current-user-principal/>"
            "</d:prop></d:propfind>"
        )
        text = await self._request("PROPFIND", self.base_url, body=body, depth="0")
        root = ElementTree.fromstring(text)
        principal = root.find(".//d:current-user-principal/d:href", NS)
        if principal is None or not principal.text:
            raise ValueError("Unable to discover CalDAV principal URL")
        return self._normalize_url(principal.text)

    async def _discover_calendar_home(self, principal_url: str) -> str:
        body = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">'
            "<d:prop><c:calendar-home-set/></d:prop>"
            "</d:propfind>"
        )
        text = await self._request("PROPFIND", principal_url, body=body, depth="0")
        root = ElementTree.fromstring(text)
        calendar_home = root.find(".//c:calendar-home-set/d:href", NS)
        if calendar_home is None or not calendar_home.text:
            raise ValueError("Unable to discover calendar home")
        return self._normalize_url(calendar_home.text)

    async def _fetch_calendars(self, calendar_home: str) -> list[CalendarInfo]:
        body = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">'
            "<d:prop><d:displayname/><d:resourcetype/></d:prop>"
            "</d:propfind>"
        )
        text = await self._request("PROPFIND", calendar_home, body=body, depth="1")
        root = ElementTree.fromstring(text)
        calendars: list[CalendarInfo] = []
        for response in root.findall("d:response", NS):
            href = response.find("d:href", NS)
            displayname = response.find(".//d:displayname", NS)
            resourcetype = response.find(".//d:resourcetype", NS)
            if href is None or not href.text or resourcetype is None:
                continue
            if resourcetype.find("c:calendar", NS) is None:
                continue
            name = displayname.text.strip() if displayname is not None and displayname.text else "Calendar"
            calendars.append(CalendarInfo(name=name, url=self._normalize_url(href.text)))
        return calendars

    async def _request(self, method: str, url: str, body: str | None = None, depth: str | None = None) -> str:
        headers = {"Content-Type": "application/xml; charset=utf-8"}
        if depth:
            headers["Depth"] = depth
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.request(
                method,
                url,
                headers=headers,
                content=body,
                auth=(self.email, self.app_password),
            )
            response.raise_for_status()
            return response.text

    def _normalize_url(self, href: str) -> str:
        if href.startswith("http://") or href.startswith("https://"):
            return href
        return urljoin(self.base_url, href.lstrip("/"))

    def _iter_calendar_data(self, xml_text: str) -> list[str]:
        root = ElementTree.fromstring(xml_text)
        calendar_data_nodes = root.findall(".//c:calendar-data", NS)
        return [node.text for node in calendar_data_nodes if node is not None and node.text]

    def _parse_ics(self, ics_text: str, fallback_tz: str | None) -> list[CalendarEvent]:
        lines = self._unfold_ics_lines(ics_text)
        events: list[CalendarEvent] = []
        current: dict[str, tuple[str, dict[str, str]]] = {}
        in_event = False

        for line in lines:
            normalized = line.strip()
            if normalized.upper() == "BEGIN:VEVENT":
                in_event = True
                current = {}
                continue
            if normalized.upper() == "END:VEVENT":
                event = self._build_event(current, fallback_tz)
                if event:
                    events.append(event)
                in_event = False
                current = {}
                continue
            if not in_event or ":" not in line:
                continue
            key, params, value = self._split_ics_line(line.rstrip())
            current[key] = (value, params)

        return events

    def _build_event(
        self, payload: dict[str, tuple[str, dict[str, str]]], fallback_tz: str | None
    ) -> CalendarEvent | None:
        if "DTSTART" not in payload:
            return None

        start_value, start_params = payload["DTSTART"]
        end_value, end_params = payload.get("DTEND", (None, {}))
        duration_value, duration_params = payload.get("DURATION", (None, {}))
        summary = payload.get("SUMMARY", (None, {}))[0]

        start_dt, is_all_day = self._parse_dt(start_value, start_params, fallback_tz)
        end_dt: datetime | date | None = None

        if end_value:
            end_dt, _ = self._parse_dt(end_value, end_params, fallback_tz)
        elif duration_value and isinstance(start_dt, datetime):
            end_dt = self._apply_duration(start_dt, duration_value)
        elif isinstance(start_dt, date):
            end_dt = start_dt + timedelta(days=1)

        if end_dt is None:
            end_dt = start_dt

        return CalendarEvent(
            start=start_dt,
            end=end_dt,
            summary=summary,
            is_all_day=is_all_day,
        )

    def _parse_dt(
        self, value: str, params: dict[str, str], fallback_tz: str | None
    ) -> tuple[datetime | date, bool]:
        if params.get("VALUE") == "DATE" or len(value) == 8:
            parsed_date = datetime.strptime(value, "%Y%m%d").date()
            return parsed_date, True

        tzid = params.get("TZID")
        if value.endswith("Z"):
            dt = datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
            return dt, False

        dt = datetime.strptime(value, "%Y%m%dT%H%M%S")
        tz = self._resolve_timezone(tzid or fallback_tz)
        return dt.replace(tzinfo=tz), False

    def _resolve_timezone(self, tz_name: str | None) -> timezone:
        if not tz_name:
            return timezone.utc
        try:
            return ZoneInfo(tz_name)
        except ZoneInfoNotFoundError:
            return timezone.utc

    def _apply_duration(self, start: datetime, duration: str) -> datetime:
        match = re.match(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?", duration)
        if not match:
            return start
        days = int(match.group(1) or 0)
        hours = int(match.group(2) or 0)
        minutes = int(match.group(3) or 0)
        seconds = int(match.group(4) or 0)
        return start + timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

    def _split_ics_line(self, line: str) -> tuple[str, dict[str, str], str]:
        left, value = line.split(":", 1)
        parts = left.split(";")
        key = parts[0].upper()
        params: dict[str, str] = {}
        for part in parts[1:]:
            if "=" in part:
                param_key, param_value = part.split("=", 1)
                params[param_key.upper()] = param_value
        return key, params, value

    def _unfold_ics_lines(self, ics_text: str) -> list[str]:
        normalized = ics_text.replace("\r\n", "\n").replace("\r", "\n")
        lines = normalized.split("\n")
        if lines and lines[0].startswith("\ufeff"):
            lines[0] = lines[0].lstrip("\ufeff")
        unfolded: list[str] = []
        for line in lines:
            if not line:
                continue
            if line.startswith(" ") or line.startswith("\t"):
                if unfolded:
                    unfolded[-1] += line.lstrip(" \t")
                continue
            unfolded.append(line.rstrip())
        return unfolded
