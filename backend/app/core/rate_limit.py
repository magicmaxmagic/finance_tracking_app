"""Rate limiting for API endpoints."""
from datetime import datetime, timedelta
from typing import Dict, Tuple
from fastapi import Request
from app.core.config import settings
from app.core.redis import get_redis


class RateLimiter:
    """Rate limiter with Redis backing and in-memory fallback."""

    def __init__(self):
        self.requests: Dict[str, list] = {}

    async def is_allowed(self, client_id: str, max_requests: int = None, window_minutes: int = 1) -> Tuple[bool, Dict]:
        """
        Check if client is allowed to make a request.

        Args:
            client_id: Unique client identifier (usually IP or user ID)
            max_requests: Max requests allowed (default from settings)
            window_minutes: Time window in minutes

        Returns:
            (allowed: bool, info: dict with current_requests, limit, reset_at)
        """
        if not settings.RATE_LIMIT_ENABLED:
            return True, {}

        max_requests = max_requests or settings.RATE_LIMIT_PER_MINUTE
        now = datetime.utcnow()

        redis_client = get_redis()
        if redis_client:
            window_seconds = int(window_minutes * 60)
            window_bucket = int(now.timestamp() // window_seconds)
            key = f"rate:{client_id}:{window_bucket}"
            current_count = await redis_client.incr(key)
            if current_count == 1:
                await redis_client.expire(key, window_seconds)
            allowed = current_count <= max_requests
            reset_at = datetime.utcfromtimestamp((window_bucket + 1) * window_seconds)
            return allowed, {
                "current_requests": current_count,
                "limit": max_requests,
                "reset_at": reset_at.isoformat(),
                "window_minutes": window_minutes,
            }

        window_start = now - timedelta(minutes=window_minutes)

        if client_id not in self.requests:
            self.requests[client_id] = []

        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > window_start
        ]

        current_count = len(self.requests[client_id])
        allowed = current_count < max_requests

        if allowed:
            self.requests[client_id].append(now)

        reset_at = self.requests[client_id][0] + timedelta(minutes=window_minutes) if self.requests[client_id] else now

        return allowed, {
            "current_requests": current_count,
            "limit": max_requests,
            "reset_at": reset_at.isoformat(),
            "window_minutes": window_minutes,
        }
    
    def get_client_id(self, request: Request) -> str:
        """Extract client identifier from request."""
        # Priority: X-Forwarded-For (proxy), then client IP
        if "x-forwarded-for" in request.headers:
            return request.headers["x-forwarded-for"].split(",")[0].strip()
        return request.client.host if request.client else "unknown"


# Global rate limiter instance
rate_limiter = RateLimiter()
