"""
Cache provider module.

Provides class to store, retrieve, and invalidate typed cached data.
"""

from abc import ABC, abstractmethod
from typing import Optional, Union, TypeVar, Generic

from redis.asyncio import Redis

from src.utils.logger import logger

T = TypeVar("T")


class CacheProvider(ABC, Generic[T]):
    """Abstract cache interface."""

    @abstractmethod
    async def get(self, **kwargs: Union[int, str]) -> Optional[T]: ...

    @abstractmethod
    async def set(self, value: T, **kwargs: Union[int, str]) -> None: ...

    @abstractmethod
    async def invalidate(self, **kwargs: Union[int, str]) -> None: ...


class RedisCacheProvider(CacheProvider[T]):
    """Generalized Redis provider"""

    def __init__(
        self, redis: Redis, key_template: str, ttl: int, sliding_ttl: bool = False
    ) -> None:
        """
        Initialization for Redis cache provider.

        redis: Redis connection instance
        key_template: Template for a value key
        ttl: Cache time-to-live in seconds, defining how long cache lives
        sliding_ttl: Whether apply Sliding TTL Strategy, when ttl is renewed upon cache read
        """
        self.redis = redis
        self.key_template = key_template
        self.ttl = ttl
        self.sliding_ttl = sliding_ttl

    async def get(self, **kwargs: Union[int, str]) -> Optional[T]:
        """
        Retrieve a cached value for the given object cache identifier.

        Args:
            obj_id (int | str): The identifier for a cache value (part of actual cache key).
        """
        key = self._build_key(**kwargs)

        raw = await self.redis.get(key)
        if raw is None:
            return None

        # For the case when connection decode_responses=False (default value)
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")

        try:
            value = self._deserialize_value(raw)
        except Exception:  # pylint: disable=broad-exception-caught
            logger.debug(
                (
                    "[CACHE ERROR] Can't load (deserialize) cache for %s. "
                    "Cache may be corrupted, malformed or value schema has changed."
                ),
                key,
            )
            await self.redis.delete(key)  # Remove unprocessable cache value
            return None

        if self.sliding_ttl:
            # Apply Sliding TTL Cache strategy
            logger.debug(
                (
                    "[CACHE SLIDE] Applied cache slide for cache key=%s "
                    "as TTL slide strategy was enabled for the %s cache provider"
                ),
                key,
                self.__class__.__name__,
            )
            await self.redis.expire(key, self.ttl)

        return value

    async def set(self, value: T, **kwargs: Union[int, str]) -> None:
        """
        Store a value in the cache for a given object cache identifier.

        Args:
            obj_id (int | str): The identifier for a cache value (part of actual cache key).
            value (T): The value to store.
        """
        key = self._build_key(**kwargs)

        try:
            raw = self._serialize_value(value)
        except Exception:  # pylint: disable=broad-exception-caught
            logger.debug("[CACHE ERROR] Can't create (serialize) cache for %s", key)
            return

        await self.redis.set(key, raw, ex=self.ttl)

    async def invalidate(self, **kwargs: Union[int, str]) -> None:
        """
        Remove a value from the cache for a given object cache identifier.

        Args:
            obj_id (int | str): The identifier for a cache value (part of actual cache key).
        """
        key = self._build_key(**kwargs)

        await self.redis.delete(key)

    def _build_key(self, **kwargs: Union[int, str]) -> str:
        """Formats cache key based on key template."""
        try:
            return self.key_template.format(**kwargs)
        except Exception as exc:
            raise ValueError(
                f"Invalid cache key template '{self.key_template}' for kwargs={kwargs}"
            ) from exc

    # Methods to be customized in a child typed class

    @abstractmethod
    def _serialize_value(self, value: T) -> str:
        """Convert value into a raw cache"""

    @abstractmethod
    def _deserialize_value(self, raw: str) -> T:
        """Convert raw cache into a value"""
