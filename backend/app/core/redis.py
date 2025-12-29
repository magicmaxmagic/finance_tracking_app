"""Redis client utilities."""
from typing import Optional
from redis.asyncio import Redis
from app.core.config import settings

_redis_client: Optional[Redis] = None


def get_redis() -> Optional[Redis]:
    """Get shared Redis client if configured."""
    global _redis_client
    if not settings.REDIS_URL:
        return None
    if _redis_client is None:
        _redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client
