"""
Cache logging utilities.

This module defines standardized cache-related events used for logging across
all cache providers.

The goal is to keep cache logs:
- consistent across different cache implementations,
- easy to grep and analyze,
- decoupled from concrete log message templates.
"""

from enum import StrEnum
from typing import Union

from src.utils.logger import logger


class CacheEvent:
    """Class for for cache-related log events."""

    class _EventType(StrEnum):
        """
        Enumeration of cache-related log events.

        These events describe *what happened* with the cache, while the surrounding
        log message provides domain-specific context (e.g. User, Contact, Count).

        Values are strings to allow:
        - direct interpolation into log messages,
        - stable log formats,
        - easy parsing by log aggregation systems.
        """

        HIT = "HIT"
        """Cache entry was successfully found and returned."""

        MISS = "MISS"
        """Cache entry was not found and a fallback (e.g. DB) was / will be used."""

        SKIPPED = "SKIPPED"
        """Cache was intentionally not used (e.g. caching / cache provider disabled)."""

        SLIDE = "SLIDE"
        """Cache TTL was extended due to sliding expiration (TTL) strategy."""

        ERROR = "ERROR"
        """An error occurred while interacting with the cache (serialization, IO, etc.)."""

    # ==========================
    # Base universal cache events creator facade
    # ==========================

    # Internal helper for potential future log unification.
    # Not used directly in provider or services.
    @classmethod
    def _log_cache_event_facade(
        cls, cache_event: _EventType, entity: str, **kwargs: Union[int, str]
    ) -> None:
        """Basic facade for cache logging with consistent format"""
        msg = entity.capitalize()

        if kwargs:
            args_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            msg = f"{msg} for {args_str}"

        logger.debug("[CACHE %s] %s", cache_event, msg)

    # ==========================
    # Provider-level cache logs (infrastructure / provider logging level)
    # ==========================

    @classmethod
    def log_cache_provider_unavailable(cls, key: str) -> None:
        """Log provider is unavailable failure."""

        logger.warning(
            "[CACHE %s] Cache provider unavailable for key=%s",
            cls._EventType.ERROR,
            key,
        )

    @classmethod
    def log_cache_deserialize_error(cls, key: str) -> None:
        """Log cache deserialization failure."""
        logger.debug(
            (
                "[CACHE %s] Can't load (deserialize) cache for %s. "
                "Cache may be corrupted, malformed or value schema has changed."
            ),
            cls._EventType.ERROR,
            key,
        )

    @classmethod
    def log_cache_serialize_error(cls, key: str) -> None:
        """Log cache serialization failure."""
        logger.debug(
            "[CACHE %s] Can't create (serialize) cache for %s",
            cls._EventType.ERROR,
            key,
        )

    @classmethod
    def log_cache_invalidate_failed(cls, key: str) -> None:
        """Log cache invalidate failure."""
        logger.warning(
            "[CACHE %s] Failed to invalidate cache key=%s",
            cls._EventType.ERROR,
            key,
        )

    @classmethod
    def log_cache_slide_failed(cls, key: str) -> None:
        """Log sliding TTL cache failure."""

        logger.debug(
            "[CACHE %s] Failed to apply sliding TTL for key=%s",
            cls._EventType.ERROR,
            key,
        )

    @classmethod
    def log_cache_slide_applied(cls, key: str, provider_name: str) -> None:
        """Log sliding TTL cache strategy application."""
        logger.debug(
            (
                "[CACHE %s] Applied cache slide for cache key=%s "
                "as TTL slide strategy was enabled for the %s cache provider"
            ),
            cls._EventType.SLIDE,
            key,
            provider_name,
        )

    # ==========================
    # Logging for USER cache events (domain-level / service logging level)
    # ==========================

    @classmethod
    def log_user_cache_hit(cls, user_id: int) -> None:
        """Log user cache HIT event."""
        logger.debug("[CACHE %s] User for user_id=%s", cls._EventType.HIT, user_id)

    @classmethod
    def log_user_cache_miss(cls, user_id: int) -> None:
        """Log user cache MISS event."""
        logger.debug("[CACHE %s] User for user_id=%s", cls._EventType.MISS, user_id)

    @classmethod
    def log_user_cache_skipped(cls) -> None:
        """Log user cache SKIPPED event."""
        logger.debug("[CACHE %s] User cache is disabled", cls._EventType.SKIPPED)

    # ==========================
    # Logging for CONTACT cache events (domain-level / service logging level)
    # ==========================

    @classmethod
    def log_contact_cache_hit(cls, user_id: int, contact_id: int) -> None:
        """Log contact cache HIT event."""
        logger.debug(
            "[CACHE %s] Contact for user_id=%s, contact_id=%s",
            cls._EventType.HIT,
            user_id,
            contact_id,
        )

    @classmethod
    def log_contact_cache_miss(cls, user_id: int, contact_id: int) -> None:
        """Log contact cache MISS event."""

        logger.debug(
            "[CACHE %s] Contact for user_id=%s, contact_id=%s",
            cls._EventType.MISS,
            user_id,
            contact_id,
        )

    @classmethod
    def log_contact_cache_skipped(cls) -> None:
        """Log contact cache SKIPPED event."""

        logger.debug("[CACHE %s] Contact cache is disabled", cls._EventType.SKIPPED)

    # ==========================
    # Logging for CONTACTS COUNT cache events (domain-level / service logging level)
    # ==========================

    @classmethod
    def log_contacts_count_cache_hit(cls, user_id: int) -> None:
        """Log contacts count cache HIT event."""

        logger.debug(
            "[CACHE %s] User contacts count for user_id=%s", cls._EventType.HIT, user_id
        )

    @classmethod
    def log_contacts_count_cache_miss(cls, user_id: int) -> None:
        """Log contacts count cache MISS event."""

        logger.debug(
            "[CACHE %s] User contacts count for user_id=%s",
            cls._EventType.MISS,
            user_id,
        )

    @classmethod
    def log_contacts_count_cache_skipped(cls) -> None:
        """Log contacts count cache SKIPPED event."""

        logger.debug(
            "[CACHE %s] User contacts count cache is disabled", cls._EventType.SKIPPED
        )
