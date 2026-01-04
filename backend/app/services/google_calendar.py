"""Google Calendar OAuth and event fetching."""
from datetime import datetime, timedelta, timezone, date
import secrets
from urllib.parse import urlencode
import httpx
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.crypto import encrypt_string, decrypt_string
from app.repositories.calendar_connection import CalendarConnectionRepository
from app.schemas.calendar import CalendarConnectionResponse, CalendarEventResponse, CalendarProvider


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]


class GoogleCalendarService:
    """Service for Google Calendar integration."""

    def __init__(self, session: AsyncSession):
        self.repository = CalendarConnectionRepository(session)

    def get_authorization_url(self, user_id: int) -> str:
        self._ensure_configured()
        state = self._create_state_token(user_id)
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(GOOGLE_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    async def handle_callback(self, code: str, state: str) -> CalendarConnectionResponse:
        self._ensure_configured()
        user_id = self._decode_state_token(state)
        token_payload = await self._exchange_code_for_tokens(code)
        refresh_token = token_payload.get("refresh_token")
        if not refresh_token:
            raise ValueError("Google did not return a refresh token. Revoke access and try again.")

        access_token = token_payload.get("access_token")
        account_email = await self._fetch_user_email(access_token)
        connection = await self.repository.upsert(
            user_id=user_id,
            provider=CalendarProvider.GOOGLE.value,
            account_email=account_email,
            calendar_name="Primary",
            calendar_url="primary",
            encrypted_secret=encrypt_string(refresh_token),
            is_active=True,
        )
        return CalendarConnectionResponse.model_validate(connection, from_attributes=True)

    async def get_connection(self, user_id: int) -> CalendarConnectionResponse | None:
        connection = await self.repository.get_by_user_provider(user_id, CalendarProvider.GOOGLE.value)
        if not connection:
            return None
        return CalendarConnectionResponse.model_validate(connection, from_attributes=True)

    async def disconnect(self, user_id: int) -> None:
        connection = await self.repository.get_by_user_provider(user_id, CalendarProvider.GOOGLE.value)
        if not connection:
            return
        await self.repository.delete(connection)

    async def list_events(
        self,
        user_id: int,
        start: date | None = None,
        end: date | None = None,
        include_details: bool = False,
    ) -> list[CalendarEventResponse]:
        connection = await self.repository.get_by_user_provider(user_id, CalendarProvider.GOOGLE.value)
        if not connection:
            raise ValueError("Google Calendar not connected")

        refresh_token = decrypt_string(connection.encrypted_secret)
        access_token = await self._refresh_access_token(refresh_token)
        calendar_id = connection.calendar_url or "primary"

        time_min = self._to_rfc3339(start) if start else None
        time_max = self._to_rfc3339(end, end_of_day=True) if end else None

        params = {
            "singleEvents": "true",
            "orderBy": "startTime",
            "maxResults": 2500,
        }
        if time_min:
            params["timeMin"] = time_min
        if time_max:
            params["timeMax"] = time_max

        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                GOOGLE_EVENTS_URL.format(calendar_id=calendar_id),
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            payload = response.json()

        events: list[CalendarEventResponse] = []
        for item in payload.get("items", []):
            start_value, is_all_day = self._parse_event_time(item.get("start", {}))
            end_value, _ = self._parse_event_time(item.get("end", {}))
            summary = item.get("summary") if include_details else "Busy"
            events.append(
                CalendarEventResponse(
                    start=start_value,
                    end=end_value or start_value,
                    summary=summary,
                    is_all_day=is_all_day,
                )
            )
        await self.repository.update(connection, last_sync_at=datetime.utcnow())
        return events

    def _ensure_configured(self) -> None:
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET or not settings.GOOGLE_REDIRECT_URI:
            raise ValueError("Google Calendar is not configured")

    def _create_state_token(self, user_id: int) -> str:
        payload = {
            "sub": str(user_id),
            "nonce": secrets.token_urlsafe(16),
            "exp": datetime.utcnow() + timedelta(minutes=10),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    def _decode_state_token(self, token: str) -> int:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return int(payload["sub"])
        except (JWTError, KeyError, ValueError) as exc:
            raise ValueError("Invalid or expired state token") from exc

    async def _exchange_code_for_tokens(self, code: str) -> dict:
        data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "code": code,
            "grant_type": "authorization_code",
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(GOOGLE_TOKEN_URL, data=data)
            response.raise_for_status()
            return response.json()

    async def _refresh_access_token(self, refresh_token: str) -> str:
        data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(GOOGLE_TOKEN_URL, data=data)
            response.raise_for_status()
            payload = response.json()
        token = payload.get("access_token")
        if not token:
            raise ValueError("Unable to refresh Google access token")
        return token

    async def _fetch_user_email(self, access_token: str) -> str:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(GOOGLE_USERINFO_URL, headers=headers)
            response.raise_for_status()
            payload = response.json()
        email = payload.get("email")
        if not email:
            raise ValueError("Unable to read Google account email")
        return email

    def _to_rfc3339(self, value: date, end_of_day: bool = False) -> str:
        dt = datetime.combine(value, datetime.max.time() if end_of_day else datetime.min.time())
        return dt.replace(tzinfo=timezone.utc).isoformat()

    def _parse_event_time(self, payload: dict) -> tuple[datetime | date, bool]:
        if "dateTime" in payload:
            dt = datetime.fromisoformat(payload["dateTime"].replace("Z", "+00:00"))
            return dt, False
        if "date" in payload:
            return date.fromisoformat(payload["date"]), True
        return datetime.utcnow(), False
