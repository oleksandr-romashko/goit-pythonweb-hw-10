"""FastAPI provider dependencies"""

from src.config import app_config
from src.providers.cloud_provider import CloudProvider, CloudinaryCloudProvider
from src.providers.avatar_provider import GravatarProvider


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
