"""
User cache module.

Provides helper functions to store, retrieve, and invalidate cached
user data (UserDTO) in Redis.
"""

import json
from typing import Optional

from src.config import app_config
from src.services.dtos import UserDTO
from src.utils.logger import logger

from .connection import get_redis

USER_KEY = "app-cache:user:{}"
CONTACT_KEY = "app-cache:contact:%s"


async def get_user_cache(user_id: int) -> Optional[UserDTO]:
    """
    Retrieve a cached UserDTO for the given user ID.

    Args:
        user_id (int): The ID of the user.

    Returns:
        Optional[UserDTO]: The cached user DTO if available, else None.
    """
    redis = get_redis()
    key = USER_KEY.format(user_id)

    raw = await redis.get(key)
    if raw is None:
        return None

    try:
        data = json.loads(raw)
    except Exception:  # pylint: disable=broad-exception-caught
        # Can't deserialize cache as it is corrupted/malformed or DTO schema changed
        logger.debug("[CACHE ERROR] Can't load (deserialize) cache for %s", key)
        await redis.delete(key)
        return None

    return UserDTO.from_dict(data)


async def set_user_cache(
    user_id: int, user_dto: UserDTO, ttl: int = app_config.CACHE_USER_TTL
) -> None:
    """
    Store a UserDTO in the cache for a given user ID.

    Args:
        user_id (int): The ID of the user.
        user_dto (UserDTO): The user DTO to cache.
        ttl (int, optional): Time-to-live in seconds. Defaults to app_config.CACHE_USER_TTL.
    """
    redis = get_redis()
    key = USER_KEY.format(user_id)

    try:
        data = json.dumps(user_dto.to_dict())
    except Exception:  # pylint: disable=broad-exception-caught
        # Can't serialize DTO, clean existing cache
        logger.debug("[CACHE ERROR] Can't create (serialize) cache for %s", key)
        return

    await redis.set(key, data, ex=ttl)


async def invalidate_user_cache(user_id: int) -> None:
    """
    Remove a cached UserDTO for a given user ID.

    Args:
        user_id (int): The ID of the user to invalidate.
    """
    redis = get_redis()
    key = USER_KEY.format(user_id)

    await redis.delete(key)
