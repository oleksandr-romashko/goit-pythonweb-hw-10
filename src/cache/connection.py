"""
Async Redis connection factory.

This module provides a lazily initialized singleton Redis client,
allowing the application to reuse a single connection pool and
avoid creating multiple Redis clients across different modules.

Usage:
------
    from src.cache.connection import get_redis

    redis = get_redis()
    await redis.set("key", "value")
    value = await redis.get("key")

The Redis connection is created only once on first use.
"""

import redis.asyncio as redis
from src.config import app_config

_redis: redis.Redis | None = None


def get_redis() -> redis.Redis:
    """
    Returns a globally shared async Redis client
    (lazy-loaded on first access).
    """
    global _redis
    if _redis is None:
        _redis = redis.from_url(
            app_config.CACHE_URL,
            encoding="utf8",
            decode_responses=True,
        )
    return _redis
