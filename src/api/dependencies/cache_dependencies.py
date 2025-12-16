"""FastAPI cache dependencies"""

from redis.asyncio import Redis

from src.providers.cache_providers.connection import get_redis, RedisDB


async def get_app_cache() -> Redis:
    """
    Dependency that returns a Redis connection
    for the application cache.
    """
    return get_redis(RedisDB.APP_CACHE)
