"""
Service layer providing high-level operations with files.

This service coordinates avatar handling logic between:
    • Cloud storage provider (upload/delete)
    • Gravatar provider (fallback avatar)
It exposes a clean API for use in FastAPI endpoints.
"""

from typing import Optional, Union, BinaryIO

from src.config import app_config
from src.providers import (
    AvatarUploadResult,
    CloudProvider,
    CloudinaryCloudProvider,
    GravatarProvider,
)
from src.providers.errors import (
    CloudAvatarUploadError,
    CloudAvatarDeletionError,
    GravatarResolveError,
)
from src.utils.logger import logger

from .dtos import UserDTO
from .errors import FileUploadFailedError


class FileService:
    """Handles business logic related to files."""

    def __init__(
        self,
        cloud_provider: CloudProvider,
        gravatar_provider: GravatarProvider,
    ):
        """Initialize the service with other services and providers."""
        self.cloud_provider = cloud_provider
        self.gravatar_provider = gravatar_provider

    async def upload_avatar(
        self, file: Union[BinaryIO, bytes], user: UserDTO
    ) -> AvatarUploadResult:
        """Upload new avatar to cloud storage and return upload metadata."""
        try:
            return await self.cloud_provider.upload_avatar(file, user)
        except CloudAvatarUploadError as exc:
            raise FileUploadFailedError(
                f"Failed to upload new avatar for user_id={user.id}"
            ) from exc

    def reset_avatar(self, user: UserDTO) -> Optional[str]:
        """Reset user's avatar to Gravatar URL, or None if not available."""
        try:
            return self.gravatar_provider.resolve_default_avatar_or_none(user.email)
        except GravatarResolveError as exc:
            # best-effort:
            # Log and return None - indicates failed resolution, but still as valid domain value
            logger.debug("Failed to fetch Gravatar for email=%s: %s", user.email, exc)
            return None

    async def delete_avatar(self, user: UserDTO) -> None:
        """
        Remove user's avatar from cloud storage.

        Best-effort --> Do not raise error, just log non-critical error
        """
        try:
            await self.cloud_provider.delete_avatar(user)
        except CloudAvatarDeletionError as exc:
            # best-effort:
            # Log and continue - deletion failures shouldn't break user flow
            logger.error(
                "Failed to delete avatar for user_id=%s avatar_url=%s: %s",
                user.id,
                user.avatar,
                exc,
            )


file_service = FileService(
    cloud_provider=CloudinaryCloudProvider(
        cloud_name=app_config.CLD_NAME,
        api_key=app_config.CLD_API_KEY,
        api_secret=app_config.CLD_API_SECRET,
    ),
    gravatar_provider=GravatarProvider(),
)
"""Default FileService instance."""
