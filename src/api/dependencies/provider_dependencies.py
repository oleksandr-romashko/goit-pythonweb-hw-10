"""FastAPI provider dependencies"""

from fastapi import Depends
from redis.asyncio import Redis

from src.config import app_config
from src.providers.cloud_provider import CloudProvider, CloudinaryCloudProvider
from src.providers.avatar_provider import GravatarProvider
from src.providers.cache_providers.contact_cache import ContactRedisCacheProvider
from src.providers.cache_providers.contacts_count_cache import (
    ContactsCountUserRedisCacheProvider,
)
from src.providers.cache_providers.user_cache import UserRedisCacheProvider

from .cache_dependencies import get_app_cache


def get_cloud_provider() -> CloudProvider:
    """Dependency provider for CloudProvider."""

    return CloudinaryCloudProvider(
        cloud_name=app_config.CLD_NAME,
        api_key=app_config.CLD_API_KEY,
        api_secret=app_config.CLD_API_SECRET,
    )


def get_gravatar_provider() -> GravatarProvider:
    """Dependency provider for GravatarProvider."""
    return GravatarProvider()


def get_contact_cache_provider(
    cache: Redis = Depends(get_app_cache),
) -> ContactRedisCacheProvider:
    """Dependency provider for ContactRedisCacheProvider."""
    return ContactRedisCacheProvider(cache)


def get_contacts_count_cache_provider(
    cache: Redis = Depends(get_app_cache),
) -> ContactsCountUserRedisCacheProvider:
    """Dependency provider for ContactsCountRedisCacheProvider."""
    return ContactsCountUserRedisCacheProvider(cache)


def get_user_cache_provider(
    cache: Redis = Depends(get_app_cache),
) -> UserRedisCacheProvider:
    """Dependency provider for UserRedisCacheProvider."""
    return UserRedisCacheProvider(cache)
