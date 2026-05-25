"""
Redis client with connection pooling and cache utilities.
"""
import json
from typing import Any, Optional

import redis.asyncio as aioredis

from app.config import settings


class RedisClient:
    """Async Redis client with helper methods."""

    def __init__(self):
        self.client: Optional[aioredis.Redis] = None

    async def connect(self):
        """Initialize Redis connection pool."""
        self.client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )
        # Verify connection
        await self.client.ping()

    async def disconnect(self):
        """Close Redis connection."""
        if self.client:
            await self.client.aclose()

    # ── Cache Operations ────────────────────────────────────────────────────────
    async def get(self, key: str) -> Optional[Any]:
        """Get a cached value, automatically deserializing JSON."""
        value = await self.client.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set a cached value, automatically serializing to JSON."""
        serialized = json.dumps(value, default=str)
        return await self.client.set(key, serialized, ex=ttl or settings.REDIS_CACHE_TTL)

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys."""
        return await self.client.delete(*keys)

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        return bool(await self.client.exists(key))

    async def invalidate_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        keys = await self.client.keys(pattern)
        if keys:
            return await self.client.delete(*keys)
        return 0

    # ── Session Management ──────────────────────────────────────────────────────
    async def set_session(self, session_id: str, data: dict, ttl: int = 86400):
        """Store session data."""
        await self.set(f"session:{session_id}", data, ttl)

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Retrieve session data."""
        return await self.get(f"session:{session_id}")

    async def delete_session(self, session_id: str):
        """Delete session data."""
        await self.delete(f"session:{session_id}")

    # ── Rate Limiting ───────────────────────────────────────────────────────────
    async def rate_limit_check(self, key: str, limit: int, window: int = 60) -> tuple[bool, int]:
        """
        Check rate limit using sliding window.
        Returns (is_allowed, remaining_requests).
        """
        pipe = self.client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        results = await pipe.execute()

        count = results[0]
        remaining = max(0, limit - count)
        return count <= limit, remaining

    # ── Pub/Sub ─────────────────────────────────────────────────────────────────
    async def publish(self, channel: str, message: Any):
        """Publish a message to a channel."""
        await self.client.publish(channel, json.dumps(message, default=str))

    def pubsub(self):
        """Get pubsub instance."""
        return self.client.pubsub()


# Global Redis client instance
redis_client = RedisClient()
