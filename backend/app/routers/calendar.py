"""Calendar router for external integrations."""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user_id
from app.db.base import get_db
from app.schemas.calendar import (
    AppleCalendarConnectRequest,
    CalendarConnectionResponse,
    CalendarEventResponse,
    CalendarInfoResponse,
    CalendarImportStatus,
    CalendarProvider,
)
from app.services.calendar_connections import CalendarConnectionService
from app.services.calendar_imports import CalendarImportService
from app.services.google_calendar import GoogleCalendarService
from app.core.config import settings


router = APIRouter(prefix="/api/calendar", tags=["calendar"])


@router.get("/apple", response_model=CalendarConnectionResponse | None)
async def get_apple_connection(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    service = CalendarConnectionService(session)
    return await service.get_connection(user_id, CalendarProvider.APPLE)


@router.post("/apple/connect", response_model=CalendarConnectionResponse)
async def connect_apple_calendar(
    payload: AppleCalendarConnectRequest,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    service = CalendarConnectionService(session)
    try:
        return await service.connect_apple(user_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/apple")
async def disconnect_apple_calendar(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    service = CalendarConnectionService(session)
    await service.disconnect(user_id, CalendarProvider.APPLE)
    return {"message": "Apple Calendar disconnected"}


@router.get("/apple/calendars", response_model=list[CalendarInfoResponse])
async def list_apple_calendars(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    service = CalendarConnectionService(session)
    try:
        return await service.list_apple_calendars(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/apple/events", response_model=list[CalendarEventResponse])
async def get_apple_events(
    start: date | None = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end: date | None = Query(default=None, description="End date (YYYY-MM-DD)"),
    include_details: bool = Query(default=False, description="Include event titles"),
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    service = CalendarConnectionService(session)
    try:
        return await service.get_apple_events(user_id, start=start, end=end, include_details=include_details)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/apple/import", response_model=CalendarImportStatus)
async def import_apple_calendar(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".ics"):
        raise HTTPException(status_code=400, detail="Only .ics files are supported")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")
    if len(content) > settings.MAX_ICS_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")
    encoding = "utf-8"
    if content.startswith(b"\xff\xfe") or content.startswith(b"\xfe\xff") or b"\x00" in content:
        encoding = "utf-16"
    try:
        ics_text = content.decode(encoding)
    except UnicodeDecodeError:
        try:
            ics_text = content.decode("utf-8")
        except UnicodeDecodeError:
            ics_text = content.decode("latin-1", errors="ignore")
    if "\x00" in ics_text:
        ics_text = ics_text.replace("\x00", "")

    service = CalendarImportService(session)
    try:
        return await service.import_ics(user_id, CalendarProvider.APPLE, ics_text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/apple/import/status", response_model=CalendarImportStatus)
async def get_apple_import_status(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    service = CalendarImportService(session)
    return await service.get_status(user_id, CalendarProvider.APPLE)


@router.get("/apple/import/events", response_model=list[CalendarEventResponse])
async def list_apple_import_events(
    start: date | None = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end: date | None = Query(default=None, description="End date (YYYY-MM-DD)"),
    include_details: bool = Query(default=False, description="Include event titles"),
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    service = CalendarImportService(session)
    return await service.list_events(
        user_id, CalendarProvider.APPLE, include_details=include_details, start=start, end=end
    )


@router.delete("/apple/import")
async def clear_apple_import_events(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    service = CalendarImportService(session)
    await service.clear_events(user_id, CalendarProvider.APPLE)
    return {"message": "Imported events cleared"}


@router.get("/google", response_model=CalendarConnectionResponse | None)
async def get_google_connection(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    service = GoogleCalendarService(session)
    return await service.get_connection(user_id)


@router.get("/google/auth-url")
async def get_google_auth_url(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    service = GoogleCalendarService(session)
    try:
        return {"url": service.get_authorization_url(user_id)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/google/callback")
async def google_oauth_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
):
    target = f"{settings.FRONTEND_URL}/planning"
    if not code or not state:
        return RedirectResponse(url=f"{target}?google=error")

    service = GoogleCalendarService(session)
    try:
        await service.handle_callback(code, state)
        return RedirectResponse(url=f"{target}?google=connected")
    except ValueError:
        return RedirectResponse(url=f"{target}?google=error")


@router.delete("/google")
async def disconnect_google_calendar(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    service = GoogleCalendarService(session)
    await service.disconnect(user_id)
    return {"message": "Google Calendar disconnected"}


@router.get("/google/events", response_model=list[CalendarEventResponse])
async def get_google_events(
    start: date | None = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end: date | None = Query(default=None, description="End date (YYYY-MM-DD)"),
    include_details: bool = Query(default=False, description="Include event titles"),
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    service = GoogleCalendarService(session)
    try:
        return await service.list_events(user_id, start=start, end=end, include_details=include_details)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
