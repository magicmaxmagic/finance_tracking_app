"""Auth repositories for token storage."""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.auth import RefreshToken, PasswordResetToken, EmailVerificationToken


class RefreshTokenRepository:
    """Repository for refresh token operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, token_hash: str, jti: str, expires_at: datetime,
                     ip_address: str | None = None, user_agent: str | None = None) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            jti=jti,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.session.add(token)
        await self.session.commit()
        await self.session.refresh(token)
        return token

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke(self, token: RefreshToken) -> RefreshToken:
        token.revoked_at = datetime.utcnow()
        self.session.add(token)
        await self.session.commit()
        await self.session.refresh(token)
        return token

    async def mark_replaced(self, token: RefreshToken, replaced_by_token_id: int) -> RefreshToken:
        token.replaced_by_token_id = replaced_by_token_id
        token.revoked_at = datetime.utcnow()
        self.session.add(token)
        await self.session.commit()
        await self.session.refresh(token)
        return token


class PasswordResetTokenRepository:
    """Repository for password reset tokens."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, token_hash: str, expires_at: datetime) -> PasswordResetToken:
        token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(token)
        await self.session.commit()
        await self.session.refresh(token)
        return token

    async def get_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        result = await self.session.execute(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def mark_used(self, token: PasswordResetToken) -> PasswordResetToken:
        token.used_at = datetime.utcnow()
        self.session.add(token)
        await self.session.commit()
        await self.session.refresh(token)
        return token


class EmailVerificationTokenRepository:
    """Repository for email verification tokens."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, token_hash: str, expires_at: datetime) -> EmailVerificationToken:
        token = EmailVerificationToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(token)
        await self.session.commit()
        await self.session.refresh(token)
        return token

    async def get_by_hash(self, token_hash: str) -> EmailVerificationToken | None:
        result = await self.session.execute(
            select(EmailVerificationToken).where(EmailVerificationToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def mark_used(self, token: EmailVerificationToken) -> EmailVerificationToken:
        token.used_at = datetime.utcnow()
        self.session.add(token)
        await self.session.commit()
        await self.session.refresh(token)
        return token
