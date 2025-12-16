"""
User cache module.

Provides helper functions to store, retrieve, and invalidate cached
user data (UserDTO) in Redis.
"""

import json
from typing import Optional


from redis.asyncio import Redis

from src.config import app_config
from src.services.dtos import UserDTO

from .cache_provider import RedisCacheProvider


class UserRedisCacheProvider(RedisCacheProvider[UserDTO]):
    """
    Redis cache provider for UserDTO.

    Contract:
    - cache key is derived from user_id (int)
    - cache value: UserDTO
    - each entry represents a snapshot of a single user
    - cache consistency is best-effort
    """

    def __init__(self, redis: Redis) -> None:
        super().__init__(
            redis=redis,
            key_template="app-cache:user:{user_id}",
            ttl=app_config.CACHE_USER_TTL,
            sliding_ttl=True,
        )

    async def get_user(self, user_id: int) -> Optional[UserDTO]:
        """
        Retrieve a cached UserDTO for the given user ID.

        Args:
            user_id (int): The ID of the user to get cache of.

        Returns:
            Optional[UserDTO]: The cached user DTO if available, else None.
        """
        return await super().get(user_id=user_id)

    async def set_user(self, user_id: int, user_dto: UserDTO) -> None:
        """
        Store a UserDTO value in the cache for a given user ID.

        Args:
            user_id (int): The ID of the user.
            user_dto (UserDTO): The UserDTO to set cache.
        """
        await super().set(user_dto, user_id=user_id)

    async def invalidate_user(self, user_id: int) -> None:
        """
        Remove a cached UserDTO for a given user ID.

        Args:
            user_id (int): The ID of the user to invalidate cache.
        """
        await super().invalidate(user_id=user_id)

    def _serialize_value(self, value: UserDTO) -> str:
        """Convert value into a raw cache"""
        return json.dumps(value.to_dict(), ensure_ascii=False)

    def _deserialize_value(self, raw: str) -> UserDTO:
        """Convert raw cache into a value"""
        data = json.loads(raw)
        return UserDTO.from_dict(data)
