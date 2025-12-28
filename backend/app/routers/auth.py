"""Auth router for authentication endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.schemas.user import UserCreate, UserLogin, TokenResponse
from app.services.user import UserService
from app.core.security import decode_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=dict)
async def register(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_db)
):
    """Register a new user."""
    service = UserService(session)
    try:
        result = await service.register(user_data)
        return {
            "user": result["user"],
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": "bearer"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=dict)
async def login(
    credentials: UserLogin,
    session: AsyncSession = Depends(get_db)
):
    """Login user."""
    service = UserService(session)
    try:
        result = await service.login(credentials.email, credentials.password)
        return {
            "user": result["user"],
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": "bearer"
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    session: AsyncSession = Depends(get_db)
):
    """Refresh access token."""
    payload = decode_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user_id = int(sub)
    service = UserService(session)
    
    try:
        user = await service.get_user(user_id)
        from app.core.security import create_access_token
        access_token = create_access_token({"sub": str(user_id)})
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    except ValueError:
        raise HTTPException(status_code=401, detail="User not found")
