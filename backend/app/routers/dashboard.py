"""Dashboard router for analytics endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.services.dashboard import DashboardService
from app.core.security import decode_token
from fastapi import Header

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def get_current_user_id(authorization: str = Header(None)) -> int:
    """Extract user ID from JWT token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization[7:]
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
    
    return int(user_id)


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
