"""Assumptions router for strategy parameters."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id
from app.db.base import get_db
from app.schemas.assumption import AssumptionCreate, AssumptionResponse
from app.services.assumption import AssumptionService

router = APIRouter(prefix="/api/assumptions", tags=["assumptions"])


@router.get("", response_model=list[AssumptionResponse])
async def list_assumptions(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """List all assumption versions."""
    service = AssumptionService(session)
    return await service.get_all_assumptions(user_id)


@router.get("/active", response_model=AssumptionResponse | None)
async def get_active_assumption(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Get the active assumption version."""
    service = AssumptionService(session)
    return await service.get_active_assumption(user_id)


@router.get("/{assumption_id}", response_model=AssumptionResponse)
async def get_assumption(
    assumption_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Get assumption version by ID."""
    service = AssumptionService(session)
    try:
        return await service.get_assumption(assumption_id, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("", response_model=AssumptionResponse)
async def create_assumption(
    payload: AssumptionCreate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Create a new assumption version."""
    service = AssumptionService(session)
    return await service.create_assumption(user_id, **payload.dict())


@router.put("/{assumption_id}/activate", response_model=AssumptionResponse)
async def activate_assumption(
    assumption_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Activate an assumption version."""
    service = AssumptionService(session)
    try:
        return await service.activate_assumption(assumption_id, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
