"""Authentication service for token management and security flows."""
from datetime import datetime, timedelta
import hashlib
import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.repositories.auth import (
    RefreshTokenRepository,
    PasswordResetTokenRepository,
    EmailVerificationTokenRepository,
)
from app.services.user import UserService


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class AuthService:
    """Service for auth token handling."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.refresh_repo = RefreshTokenRepository(session)
        self.password_reset_repo = PasswordResetTokenRepository(session)
        self.email_verification_repo = EmailVerificationTokenRepository(session)
        self.user_service = UserService(session)

    async def issue_token_pair(self, user_id: int, ip_address: str | None = None,
                               user_agent: str | None = None) -> tuple[str, str]:
        access_token = create_access_token({"sub": str(user_id)})
        refresh_token = create_refresh_token({"sub": str(user_id)})
        refresh_payload = decode_token(refresh_token, token_type="refresh")
        refresh_exp = datetime.utcfromtimestamp(refresh_payload["exp"])
        refresh_jti = refresh_payload.get("jti", "")
        await self.refresh_repo.create(
            user_id=user_id,
            token_hash=_hash_token(refresh_token),
            jti=refresh_jti,
            expires_at=refresh_exp,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return access_token, refresh_token

    async def rotate_refresh_token(self, refresh_token: str, ip_address: str | None = None,
                                   user_agent: str | None = None) -> tuple[str, str]:
        payload = decode_token(refresh_token, token_type="refresh")
        if not payload:
            raise ValueError("Invalid or expired refresh token")

        token_hash = _hash_token(refresh_token)
        stored_token = await self.refresh_repo.get_by_hash(token_hash)
        if not stored_token or stored_token.revoked_at:
            raise ValueError("Refresh token revoked")

        if stored_token.expires_at < datetime.utcnow():
            raise ValueError("Refresh token expired")

        user_id = int(payload["sub"])
        access_token = create_access_token({"sub": str(user_id)})
        new_refresh_token = create_refresh_token({"sub": str(user_id)})
        new_payload = decode_token(new_refresh_token, token_type="refresh")
        new_exp = datetime.utcfromtimestamp(new_payload["exp"])
        new_jti = new_payload.get("jti", "")
        new_record = await self.refresh_repo.create(
            user_id=user_id,
            token_hash=_hash_token(new_refresh_token),
            jti=new_jti,
            expires_at=new_exp,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.refresh_repo.mark_replaced(stored_token, new_record.id)
        return access_token, new_refresh_token

    async def revoke_refresh_token(self, refresh_token: str) -> None:
        token_hash = _hash_token(refresh_token)
        stored_token = await self.refresh_repo.get_by_hash(token_hash)
        if stored_token and not stored_token.revoked_at:
            await self.refresh_repo.revoke(stored_token)

    async def create_password_reset_token(self, email: str) -> str:
        user = await self.user_service.repository.get_by_email(email)
        if not user:
            return ""
        token = secrets.token_urlsafe(32)
        token_hash = _hash_token(token)
        expires_at = datetime.utcnow() + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
        await self.password_reset_repo.create(user_id=user.id, token_hash=token_hash, expires_at=expires_at)
        return token

    async def reset_password(self, token: str, new_password: str) -> None:
        token_hash = _hash_token(token)
        record = await self.password_reset_repo.get_by_hash(token_hash)
        if not record or record.used_at:
            raise ValueError("Invalid token")
        if record.expires_at < datetime.utcnow():
            raise ValueError("Token expired")
        await self.user_service.update_user(record.user_id, password=new_password)
        await self.password_reset_repo.mark_used(record)

    async def create_email_verification_token(self, email: str) -> str:
        user = await self.user_service.repository.get_by_email(email)
        if not user:
            return ""
        token = secrets.token_urlsafe(32)
        token_hash = _hash_token(token)
        expires_at = datetime.utcnow() + timedelta(hours=settings.EMAIL_VERIFY_TOKEN_EXPIRE_HOURS)
        await self.email_verification_repo.create(user_id=user.id, token_hash=token_hash, expires_at=expires_at)
        return token

    async def verify_email(self, token: str) -> None:
        token_hash = _hash_token(token)
        record = await self.email_verification_repo.get_by_hash(token_hash)
        if not record or record.used_at:
            raise ValueError("Invalid token")
        if record.expires_at < datetime.utcnow():
            raise ValueError("Token expired")
        await self.user_service.repository.update(record.user_id, is_email_verified=True)
        await self.email_verification_repo.mark_used(record)
