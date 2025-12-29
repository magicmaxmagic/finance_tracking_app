"""Token blacklist for logout functionality."""
from datetime import datetime
from typing import Set, Optional
from app.core.config import settings
from app.core.redis import get_redis


class TokenBlacklist:
    """Token blacklist with Redis backing and in-memory fallback."""

    def __init__(self):
        self.blacklisted_tokens: Set[str] = set()

    async def add_token(self, jti: str, expires_at: Optional[datetime] = None) -> None:
        """Add token jti to blacklist until it expires."""
        if not settings.ENABLE_TOKEN_BLACKLIST:
            return
        redis_client = get_redis()
        if redis_client:
            key = f"{settings.TOKEN_BLACKLIST_PREFIX}{jti}"
            if expires_at:
                ttl_seconds = max(0, int((expires_at - datetime.utcnow()).total_seconds()))
                await redis_client.set(key, "1", ex=ttl_seconds)
            else:
                await redis_client.set(key, "1")
            return
        self.blacklisted_tokens.add(jti)

    async def is_blacklisted(self, jti: str) -> bool:
        """Check if token jti is blacklisted."""
        if not settings.ENABLE_TOKEN_BLACKLIST:
            return False
        redis_client = get_redis()
        if redis_client:
            key = f"{settings.TOKEN_BLACKLIST_PREFIX}{jti}"
            exists = await redis_client.exists(key)
            return bool(exists)
        return jti in self.blacklisted_tokens

    def clear(self) -> None:
        """Clear all blacklisted tokens."""
        self.blacklisted_tokens.clear()

    def get_stats(self) -> dict:
        """Get blacklist statistics."""
        return {
            "total_blacklisted": len(self.blacklisted_tokens),
            "enabled": settings.ENABLE_TOKEN_BLACKLIST,
        }


# Global token blacklist instance
token_blacklist = TokenBlacklist()
