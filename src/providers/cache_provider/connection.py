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

from enum import Enum

from redis.asyncio import Redis, from_url

from src.config import app_config


class RedisDB(Enum):
    """
    Enumerates Redis logical databases.

    API_CACHE — base for app caching of users, contacts, etc.
    RATELIMIT — base for a rate limiter.
    """

    APP_CACHE = 0
    RATELIMIT = 1


_connections: dict[RedisDB, Redis] = {}


def get_redis(redis_db: RedisDB = RedisDB.APP_CACHE) -> Redis:
    """
    Return a Redis connection for the specified logical database.

    This function lazily initializes a Redis connection for the given database
    and caches it for future use (singleton per database).

    Args:
        redis_db (RedisDB, optional): Logical Redis database to connect to.
            Defaults to RedisDB.APP_CACHE.

    Returns:
        Redis: An instance of `redis.asyncio.Redis` connected to the chosen database.
    """
    if redis_db not in _connections:
        url = f"{app_config.CACHE_URL_BASE}/{redis_db.value}"
        _connections[redis_db] = from_url(url, encoding="utf8", decode_responses=True)
    return _connections[redis_db]
