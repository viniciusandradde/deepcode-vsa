"""Redis cache utility for API response caching.

Provides get_cached() / set_cached() with TTL for short-lived caching
of GLPI, Zabbix, and Linear API responses. Uses the same Redis instance
already running for Celery (REDIS_URL env var).

Design: fire-and-forget — cache errors never propagate to callers.
"""

import json
import logging
import os

import redis

logger = logging.getLogger(__name__)

_pool: redis.ConnectionPool | None = None


def _get_pool() -> redis.ConnectionPool:
    global _pool
    if _pool is None:
        url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        _pool = redis.ConnectionPool.from_url(url, decode_responses=True)
    return _pool


def get_cached(key: str) -> dict | list | None:
    """Get cached value. Returns None on miss or error."""
    try:
        r = redis.Redis(connection_pool=_get_pool())
        data = r.get(key)
        return json.loads(data) if data else None
    except Exception as e:
        logger.debug("Cache miss/error for %s: %s", key, e)
        return None


def set_cached(key: str, value, ttl_seconds: int = 120):
    """Cache value with TTL. Fire-and-forget, never raises."""
    try:
        r = redis.Redis(connection_pool=_get_pool())
        r.setex(key, ttl_seconds, json.dumps(value, default=str))
    except Exception as e:
        logger.debug("Cache set failed for %s: %s", key, e)


def invalidate(pattern: str):
    """Delete keys matching a pattern (e.g. 'glpi:*'). Fire-and-forget."""
    try:
        r = redis.Redis(connection_pool=_get_pool())
        keys = r.keys(pattern)
        if keys:
            r.delete(*keys)
            logger.debug("Invalidated %d keys matching %s", len(keys), pattern)
    except Exception as e:
        logger.debug("Cache invalidate failed for %s: %s", pattern, e)
