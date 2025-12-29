"""Audit log service."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.audit_log import AuditLogRepository
from app.core.config import settings


class AuditLogService:
    """Service for audit logging."""

    def __init__(self, session: AsyncSession):
        self.repository = AuditLogRepository(session)
        self.session = session

    async def log(self, action: str, user_id: int | None = None, ip_address: str | None = None,
                  user_agent: str | None = None, details: dict | None = None) -> None:
        if not settings.AUDIT_LOG_ENABLED:
            return
        await self.repository.create(
            action=action,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
        )
