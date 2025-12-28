"""Net worth router for net worth endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.services.net_worth import NetWorthService
from app.core.security import decode_token
from fastapi import Header

router = APIRouter(prefix="/api/net-worth", tags=["net-worth"])


def get_current_user_id(authorization: str = Header(None)) -> int:
    """Extract user ID from JWT token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization[7:]
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return int(sub)


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
