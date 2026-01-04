"""Scenario router for strategy simulations."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id
from app.db.base import get_db
from app.schemas.scenario import ScenarioCreate, ScenarioUpdate, ScenarioResponse
from app.services.scenario import ScenarioService

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioResponse])
async def list_scenarios(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """List all scenarios."""
    service = ScenarioService(session)
    return await service.get_all_scenarios(user_id)


@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(
    scenario_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Get scenario by ID."""
    service = ScenarioService(session)
    try:
        return await service.get_scenario(scenario_id, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("", response_model=ScenarioResponse)
async def create_scenario(
    payload: ScenarioCreate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Create a scenario."""
    service = ScenarioService(session)
    return await service.create_scenario(user_id, **payload.dict())


@router.put("/{scenario_id}", response_model=ScenarioResponse)
async def update_scenario(
    scenario_id: int,
    payload: ScenarioUpdate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Create a new scenario version."""
    service = ScenarioService(session)
    try:
        return await service.update_scenario(scenario_id, user_id, **payload.dict(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{scenario_id}")
async def delete_scenario(
    scenario_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Delete a scenario."""
    service = ScenarioService(session)
    try:
        await service.delete_scenario(scenario_id, user_id)
        return {"message": "Scenario deleted"}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
