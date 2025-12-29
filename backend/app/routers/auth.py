"""Auth router for authentication endpoints."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.schemas.user import UserCreate, UserLogin
from app.schemas.auth import (
    PasswordResetRequest,
    PasswordResetConfirm,
    EmailVerificationRequest,
    EmailVerificationConfirm,
)
from app.services.user import UserService
from app.services.auth import AuthService
from app.services.audit_log import AuditLogService
from app.core.security import decode_token
from app.core.rate_limit import rate_limiter
from app.core.token_blacklist import token_blacklist
from app.core.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set auth cookies for access and refresh tokens."""
    response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(settings.ACCESS_TOKEN_COOKIE_NAME, domain=settings.COOKIE_DOMAIN)
    response.delete_cookie(settings.REFRESH_TOKEN_COOKIE_NAME, domain=settings.COOKIE_DOMAIN)


@router.post("/register", response_model=dict)
async def register(
    user_data: UserCreate,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db)
):
    """Register a new user."""
    service = UserService(session)
    auth_service = AuthService(session)
    audit_service = AuditLogService(session)
    try:
        result = await service.register(user_data)
        access_token, refresh_token = await auth_service.issue_token_pair(
            result["user"].id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
        )
        _set_auth_cookies(response, access_token, refresh_token)
        await audit_service.log(
            action="user.registered",
            user_id=result["user"].id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
        )
        return {
            "user": result["user"],
            "token_type": "bearer",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=dict)
async def login(
    credentials: UserLogin,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db)
):
    """Login user with rate limiting."""
    # Rate limiting (5 attempts per minute max)
    client_id = rate_limiter.get_client_id(request)
    allowed, rate_info = await rate_limiter.is_allowed(client_id, max_requests=5, window_minutes=1)
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Try again in {rate_info['window_minutes']} minute(s)"
        )
    
    service = UserService(session)
    auth_service = AuthService(session)
    audit_service = AuditLogService(session)
    try:
        result = await service.login(credentials.email, credentials.password)
        access_token, refresh_token = await auth_service.issue_token_pair(
            result["user"].id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
        )
        _set_auth_cookies(response, access_token, refresh_token)
        await audit_service.log(
            action="user.login",
            user_id=result["user"].id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
        )
        return {
            "user": result["user"],
            "token_type": "bearer"
        }
    except ValueError as e:
        await audit_service.log(
            action="user.login_failed",
            user_id=None,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
            details={"email": credentials.email},
        )
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/refresh")
async def refresh_access_token(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db)
):
    """Refresh access token with rotation."""
    refresh_token = request.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    auth_service = AuthService(session)
    audit_service = AuditLogService(session)
    try:
        access_token, new_refresh_token = await auth_service.rotate_refresh_token(
            refresh_token,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
        )
        _set_auth_cookies(response, access_token, new_refresh_token)
        await audit_service.log(
            action="user.refresh",
            user_id=None,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
        )
        return {"token_type": "bearer"}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db)
):
    """Logout user (blacklist token)."""
    auth_service = AuthService(session)
    audit_service = AuditLogService(session)
    access_token = request.cookies.get(settings.ACCESS_TOKEN_COOKIE_NAME)
    refresh_token = request.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)

    user_id = None
    if access_token:
        payload = decode_token(access_token, token_type="access")
        if payload and payload.get("jti"):
            expires_at = datetime.utcfromtimestamp(payload.get("exp"))
            await token_blacklist.add_token(payload["jti"], expires_at)
            sub = payload.get("sub")
            if sub:
                user_id = int(sub)

    if refresh_token:
        await auth_service.revoke_refresh_token(refresh_token)

    _clear_auth_cookies(response)
    await audit_service.log(
        action="user.logout",
        user_id=user_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    return {
        "message": "Successfully logged out",
        "blacklist_stats": token_blacklist.get_stats(),
    }


@router.post("/request-password-reset")
async def request_password_reset(
    payload: PasswordResetRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """Request a password reset token."""
    auth_service = AuthService(session)
    audit_service = AuditLogService(session)
    token = await auth_service.create_password_reset_token(payload.email)
    await audit_service.log(
        action="user.password_reset_requested",
        user_id=None,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
        details={"email": payload.email},
    )
    response_data = {"message": "If the account exists, a reset email was sent."}
    if settings.DEBUG and token:
        response_data["token"] = token
    return response_data


@router.post("/reset-password")
async def reset_password(
    payload: PasswordResetConfirm,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """Reset password using a token."""
    auth_service = AuthService(session)
    audit_service = AuditLogService(session)
    try:
        await auth_service.reset_password(payload.token, payload.new_password)
        await audit_service.log(
            action="user.password_reset_completed",
            user_id=None,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
        )
        return {"message": "Password updated successfully."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/request-email-verification")
async def request_email_verification(
    payload: EmailVerificationRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """Request an email verification token."""
    auth_service = AuthService(session)
    audit_service = AuditLogService(session)
    token = await auth_service.create_email_verification_token(payload.email)
    await audit_service.log(
        action="user.email_verification_requested",
        user_id=None,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
        details={"email": payload.email},
    )
    response_data = {"message": "If the account exists, a verification email was sent."}
    if settings.DEBUG and token:
        response_data["token"] = token
    return response_data


@router.post("/verify-email")
async def verify_email(
    payload: EmailVerificationConfirm,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """Verify email address using a token."""
    auth_service = AuthService(session)
    audit_service = AuditLogService(session)
    try:
        await auth_service.verify_email(payload.token)
        await audit_service.log(
            action="user.email_verified",
            user_id=None,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
        )
        return {"message": "Email verified successfully."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
