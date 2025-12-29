"""Dashboard router for analytics endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.services.dashboard import DashboardService
from app.core.deps import get_current_user_id

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
async def get_dashboard_data(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Get complete dashboard data."""
    service = DashboardService(session)
    try:
        return await service.get_dashboard_data(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
