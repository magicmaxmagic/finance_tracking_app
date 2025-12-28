"""User router for user management endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.schemas.user import UserResponse, UserUpdate
from app.services.user import UserService
from app.core.security import decode_token
from fastapi import Header

router = APIRouter(prefix="/api/users", tags=["users"])


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


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Get current user information."""
    service = UserService(session)
    try:
        return await service.get_user(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Update current user."""
    service = UserService(session)
    try:
        update_data = user_data.dict(exclude_unset=True)
        return await service.update_user(user_id, **update_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
