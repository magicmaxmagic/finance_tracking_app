"""Goals router for financial targets."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id
from app.db.base import get_db
from app.schemas.goal import FinancialGoalCreate, FinancialGoalUpdate, FinancialGoalResponse
from app.services.goal import GoalService

router = APIRouter(prefix="/api/goals", tags=["goals"])


@router.get("", response_model=list[FinancialGoalResponse])
async def list_goals(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Get all financial goals."""
    service = GoalService(session)
    return await service.get_all_goals(user_id)


@router.get("/active", response_model=FinancialGoalResponse | None)
async def get_active_goal(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Get active financial goal."""
    service = GoalService(session)
    return await service.get_active_goal(user_id)


@router.get("/{goal_id}", response_model=FinancialGoalResponse)
async def get_goal(
    goal_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Get goal by ID."""
    service = GoalService(session)
    try:
        return await service.get_goal(goal_id, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("", response_model=FinancialGoalResponse)
async def create_goal(
    payload: FinancialGoalCreate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Create a financial goal."""
    service = GoalService(session)
    return await service.create_goal(user_id, **payload.dict())


@router.put("/{goal_id}", response_model=FinancialGoalResponse)
async def update_goal(
    goal_id: int,
    payload: FinancialGoalUpdate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Update a financial goal."""
    service = GoalService(session)
    try:
        return await service.update_goal(goal_id, user_id, **payload.dict(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Delete a financial goal."""
    service = GoalService(session)
    try:
        await service.delete_goal(goal_id, user_id)
        return {"message": "Goal deleted"}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
