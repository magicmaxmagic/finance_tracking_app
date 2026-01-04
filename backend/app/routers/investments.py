"""Investment router for asset management endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.schemas.investment import InvestmentCreate, InvestmentUpdate, InvestmentResponse
from app.services.investment import InvestmentService
from app.core.deps import get_current_user_id

router = APIRouter(prefix="/api/investments", tags=["investments"])


@router.get("", response_model=list[InvestmentResponse])
async def get_investments(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Get all investment assets for current user."""
    service = InvestmentService(session)
    return await service.get_all_investments(user_id)


@router.get("/{investment_id}", response_model=InvestmentResponse)
async def get_investment(
    investment_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Get investment asset by ID."""
    service = InvestmentService(session)
    try:
        return await service.get_investment(investment_id, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("", response_model=InvestmentResponse)
async def create_investment(
    payload: InvestmentCreate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Create a new investment asset."""
    service = InvestmentService(session)
    return await service.create_investment(user_id, **payload.dict())


@router.put("/{investment_id}", response_model=InvestmentResponse)
async def update_investment(
    investment_id: int,
    payload: InvestmentUpdate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Update investment asset."""
    service = InvestmentService(session)
    try:
        update_data = payload.dict(exclude_unset=True)
        return await service.update_investment(investment_id, user_id, **update_data)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{investment_id}")
async def delete_investment(
    investment_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Delete investment asset."""
    service = InvestmentService(session)
    try:
        await service.delete_investment(investment_id, user_id)
        return {"message": "Investment asset deleted successfully"}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
