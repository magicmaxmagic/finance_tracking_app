"""Budget router for budget management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse, BudgetWithSpent
from app.services.budget import BudgetService
from app.core.security import decode_token
from fastapi import Header
from datetime import date

router = APIRouter(prefix="/api/budgets", tags=["budgets"])


def get_current_user_id(authorization: str = Header(None)) -> int:
    """Extract user ID from JWT token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization[7:]
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
    
    return int(user_id)


@router.get("", response_model=list[BudgetResponse])
async def get_budgets(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Get all budgets for current user."""
    service = BudgetService(session)
    return await service.get_all_budgets(user_id)


@router.get("/month/{month}", response_model=list[BudgetWithSpent])
async def get_budgets_by_month(
    month: str,  # Format: YYYY-MM
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Get budgets for a specific month with spent amounts."""
    service = BudgetService(session)
    try:
        month_date = date.fromisoformat(f"{month}-01")
        return await service.get_budgets_with_spent(user_id, month_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid month format (use YYYY-MM)")


@router.get("/{budget_id}", response_model=BudgetResponse)
async def get_budget(
    budget_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Get budget by ID."""
    service = BudgetService(session)
    try:
        return await service.get_budget(budget_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=BudgetResponse)
async def create_budget(
    budget_data: BudgetCreate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Create a new budget."""
    service = BudgetService(session)
    try:
        return await service.create_budget(user_id, **budget_data.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: int,
    budget_data: BudgetUpdate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Update budget."""
    service = BudgetService(session)
    try:
        update_data = budget_data.dict(exclude_unset=True)
        return await service.update_budget(budget_id, user_id, **update_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{budget_id}")
async def delete_budget(
    budget_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Delete budget."""
    service = BudgetService(session)
    try:
        await service.delete_budget(budget_id, user_id)
        return {"message": "Budget deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
