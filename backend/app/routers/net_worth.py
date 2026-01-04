"""Net worth router for net worth endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.services.net_worth import NetWorthService
from app.core.deps import get_current_user_id

router = APIRouter(prefix="/api/net-worth", tags=["net-worth"])


@router.get("/summary")
async def get_net_worth_summary(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Get current net worth summary."""
    service = NetWorthService(session)
    try:
        return await service.get_net_worth_summary(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history")
async def get_net_worth_history(
    start_date: str,  # Format: YYYY-MM-DD
    end_date: str,    # Format: YYYY-MM-DD
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Get net worth history for a date range."""
    service = NetWorthService(session)
    try:
        from datetime import date
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        return await service.get_net_worth_history(user_id, start, end)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format (use YYYY-MM-DD)")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/snapshot")
async def capture_net_worth_snapshot(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Capture net worth snapshot for all active accounts."""
    service = NetWorthService(session)
    try:
        return await service.capture_snapshot(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
