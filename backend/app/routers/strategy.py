"""Strategy router for planning and decision intelligence."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id
from app.db.base import get_db
from app.schemas.strategy import (
    TrajectoryRequest,
    TrajectoryResponse,
    ScenarioCompareRequest,
    ScenarioComparisonResponse,
    DecisionOverview,
    StrategyAlert,
)
from app.services.strategy import StrategyService

router = APIRouter(prefix="/api/strategy", tags=["strategy"])


@router.post("/trajectory", response_model=TrajectoryResponse)
async def get_trajectory(
    payload: TrajectoryRequest,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Run a deterministic trajectory simulation."""
    service = StrategyService(session)
    try:
        return await service.run_trajectory(user_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/scenarios/compare", response_model=ScenarioComparisonResponse)
async def compare_scenarios(
    payload: ScenarioCompareRequest,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Compare scenario outcomes."""
    service = StrategyService(session)
    try:
        return await service.compare_scenarios(user_id, payload.scenario_ids)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/decisions", response_model=DecisionOverview)
async def decision_overview(
    goal_id: int | None = Query(None),
    assumption_id: int | None = Query(None),
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Get decision impact ranking and recommendations."""
    service = StrategyService(session)
    try:
        return await service.get_decision_overview(user_id, goal_id, assumption_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/alerts", response_model=StrategyAlert)
async def strategy_alert(
    goal_id: int | None = Query(None),
    assumption_id: int | None = Query(None),
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Get deviation alerts for the active trajectory."""
    service = StrategyService(session)
    return await service.get_alert(user_id, goal_id, assumption_id)
