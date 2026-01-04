"""Onboarding router for investor profiling."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id
from app.db.base import get_db
from app.schemas.onboarding import OnboardingProfileCreate, OnboardingProfileResponse, OnboardingStatus
from app.services.onboarding import OnboardingService

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


@router.get("/status", response_model=OnboardingStatus)
async def onboarding_status(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Check onboarding completion status."""
    service = OnboardingService(session)
    completed = await service.get_status(user_id)
    return OnboardingStatus(is_completed=completed)


@router.get("", response_model=OnboardingProfileResponse | None)
async def onboarding_profile(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Get onboarding profile."""
    service = OnboardingService(session)
    return await service.get_profile(user_id)


@router.post("/complete", response_model=OnboardingProfileResponse)
async def complete_onboarding(
    payload: OnboardingProfileCreate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Complete onboarding flow."""
    service = OnboardingService(session)
    try:
        return await service.complete_onboarding(user_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
