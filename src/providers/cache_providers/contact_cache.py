"""
Contact cache module.

Provides helper functions to store, retrieve, and invalidate cached
contact data (ContactDTO) in Redis.
"""

import json
from typing import Optional


from redis.asyncio import Redis

from src.config import app_config
from src.services.dtos import ContactDTO

from .cache_provider import RedisCacheProvider


class ContactRedisCacheProvider(RedisCacheProvider[ContactDTO]):
    """
    Redis cache provider for ContactDTO.

    Contract:
    - cache key is derived from user_id (int) and contact_id (int)
    - cache value: ContactDTO
    - each entry represents a snapshot of a single contact
    - cache consistency is best-effort
    """

    def __init__(self, redis: Redis) -> None:
        super().__init__(
            redis=redis,
            key_template="app-cache:user:{user_id}:contact:{contact_id}",
            ttl=app_config.CACHE_USER_TTL,
            sliding_ttl=True,
        )

    async def get_contact(self, user_id: int, contact_id: int) -> Optional[ContactDTO]:
        """
        Retrieve a cached ContactDTO for the given user ID and contact ID.

        Args:
            user_id (int): The ID of the user - owner of the contact.
            contact_id (int): The ID of the contact to get cache of.

        Returns:
            Optional[ContactDTO]: The cached contact DTO if available, else None.
        """
        return await super().get(user_id=user_id, contact_id=contact_id)

    async def set_contact(
        self, user_id: int, contact_id: int, contact_dto: ContactDTO
    ) -> None:
        """
        Store a ContactDTO value in the cache for a given user ID and contact ID.

        Args:
            user_id (int): The ID of the user owning the contact.
            contact_id (int): The ID of the contact.
            contact_dto (ContactDTO): The ContactDTO to set cache.
        """
        await super().set(contact_dto, user_id=user_id, contact_id=contact_id)

    async def invalidate_contact(self, user_id: int, contact_id: int) -> None:
        """
        Remove a cached ContactDTO for a given user ID and contact_id.

        Args:
            user_id (int): The ID of the user owning the contact.
            contact_id (int): The ID of the contact to invalidate cache.
        """
        await super().invalidate(user_id=user_id, contact_id=contact_id)

    def _serialize_value(self, value: ContactDTO) -> str:
        """Convert value into a raw cache"""
        return json.dumps(value.to_dict(), ensure_ascii=False)

    def _deserialize_value(self, raw: str) -> ContactDTO:
        """Convert raw cache into a value"""
        data = json.loads(raw)
        return ContactDTO.from_dict(data)
