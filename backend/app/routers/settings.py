"""Settings router for user preferences."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id
from app.db.base import get_db
from app.schemas.settings import SettingsResponse, SettingsUpdate
from app.services.settings import SettingsService

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
async def get_settings(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Get user settings."""
    service = SettingsService(session)
    return await service.get_settings(user_id)


@router.put("", response_model=SettingsResponse)
async def update_settings(
    payload: SettingsUpdate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Update user settings."""
    service = SettingsService(session)
    return await service.update_settings(user_id, payload)


@router.post("/calendar-feed/rotate", response_model=SettingsResponse)
async def rotate_calendar_feed(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Rotate the public calendar feed token."""
    service = SettingsService(session)
    return await service.rotate_calendar_feed_token(user_id)
