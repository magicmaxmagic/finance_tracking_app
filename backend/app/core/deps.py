"""Shared dependencies for routers."""
from fastapi import Header, HTTPException, status, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import validate_access_token
from app.core.config import settings
from app.db.base import get_db
from app.services.user import UserService


async def get_current_user_id(
    request: Request,
    authorization: str = Header(None),
    session: AsyncSession = Depends(get_db),
) -> int:
    """Extract and validate user ID from access token."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    if not token:
        token = request.cookies.get(settings.ACCESS_TOKEN_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid authorization header")
    payload = await validate_access_token(token)

    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: missing user ID")

    service = UserService(session)
    user = await service.get_user(int(user_id))
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")

    request.state.user_id = int(user_id)
    return int(user_id)
