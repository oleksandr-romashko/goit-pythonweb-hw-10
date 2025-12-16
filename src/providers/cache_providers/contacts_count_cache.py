"""
User cache module.

Provides helper functions to store, retrieve, and invalidate cached
user contacts count data (int) in Redis.
"""

import json
from typing import Optional


from redis.asyncio import Redis

from src.config import app_config

from .cache_provider import RedisCacheProvider


class ContactsCountUserRedisCacheProvider(RedisCacheProvider[int]):
    """
    Redis cache provider for contacts count.

    Contract:
    - cache key is derived from user_id (int)
    - cache value: int (contacts count)
    - cache entries represent a number of contacts user has
    - cache consistency is best-effort
    """

    def __init__(self, redis: Redis) -> None:
        super().__init__(
            redis=redis,
            key_template="app-cache:user:{user_id}:contacts-count",
            ttl=app_config.CACHE_CONTACTS_COUNT_TTL,
            sliding_ttl=True,
        )

    async def get_contacts_count(self, user_id: int) -> Optional[int]:
        """
        Retrieve contacts count for a given user by user ID.

        Args:
            user_id (int): The ID of the user to get contacts count.

        Returns:
            Optional[int]: Contacts count if available, else None.
        """
        return await super().get(user_id=user_id)

    async def set_contacts_count(self, user_id: int, count: int) -> None:
        """
        Store a contacts count value in the cache for a given user ID.

        Args:
            user_id (int): The ID of the user.
            count (int): Contacts count to set cache.
        """
        await super().set(count, user_id=user_id)

    async def invalidate_contacts_count(self, user_id: int) -> None:
        """
        Remove a cached contacts count for a given user ID.

        Args:
            user_id (int): The ID of the user to invalidate cache.
        """
        await super().invalidate(user_id=user_id)

    def _serialize_value(self, value: int) -> str:
        """Convert value into a raw cache"""
        return json.dumps(value)

    def _deserialize_value(self, raw: str) -> int:
        """Convert raw cache into a value"""
        return json.loads(raw)
