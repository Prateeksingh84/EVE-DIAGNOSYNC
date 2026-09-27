import json
import time
from typing import Any, Optional

import redis.asyncio as redis
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

_redis_pool: Optional[redis.Redis] = None
_last_failed_attempt: float = 0
_RETRY_INTERVAL: float = 60.0  # Retry every 60 seconds if Redis was down


async def get_redis() -> Optional[redis.Redis]:
    """Get or create a Redis connection. Gracefully bypasses if Redis is unreachable."""
    global _redis_pool, _last_failed_attempt
    if _redis_pool is not None:
        return _redis_pool

    now = time.time()
    if now - _last_failed_attempt < _RETRY_INTERVAL:
        return None

    try:
        pool = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=1,
        )
        await pool.ping()
        _redis_pool = pool
        logger.info("redis_connected", url=settings.REDIS_URL)
        return _redis_pool
    except Exception as e:
        _last_failed_attempt = now
        logger.warning(
            "redis_connection_failed",
            error=str(e),
            message="Continuing without cache (will retry in 60s)",
        )
        _redis_pool = None
        return None


async def cache_get(key: str) -> Optional[Any]:
    """Get a value from cache. Returns None on miss or error."""
    try:
        r = await get_redis()
        if r is None:
            return None
        value = await r.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        logger.warning("cache_get_error", key=key, error=str(e))
    return None


async def cache_set(
    key: str, data: Any, ttl: int = 300
) -> None:
    """Set a value in cache with TTL (default 5 minutes)."""
    try:
        r = await get_redis()
        if r is None:
            return
        await r.setex(key, ttl, json.dumps(data, default=str))
    except Exception as e:
        logger.warning("cache_set_error", key=key, error=str(e))


async def cache_delete(key: str) -> None:
    """Delete a key from cache."""
    try:
        r = await get_redis()
        if r is None:
            return
        await r.delete(key)
    except Exception as e:
        logger.warning("cache_delete_error", key=key, error=str(e))


async def cache_delete_pattern(pattern: str) -> None:
    """Delete all keys matching a pattern."""
    try:
        r = await get_redis()
        if r is None:
            return
        async for key in r.scan_iter(match=pattern):
            await r.delete(key)
    except Exception as e:
        logger.warning(
            "cache_delete_pattern_error", pattern=pattern, error=str(e)
        )


async def close_redis() -> None:
    """Close the Redis connection pool."""
    global _redis_pool
    if _redis_pool:
        await _redis_pool.close()
        _redis_pool = None
        logger.info("redis_disconnected")
