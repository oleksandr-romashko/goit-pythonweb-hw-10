"""
Service layer providing high-level operations with files.

This service coordinates avatar handling logic between:
    • Cloud storage provider (upload/delete)
    • Gravatar provider (fallback avatar)
It exposes a clean API for use in FastAPI endpoints.
"""

from typing import Optional

from fastapi import UploadFile

from src.config import app_config
from src.providers.avatar_provider import GravatarProvider
from src.providers.cloud_provider import CloudProvider, AvatarUploadResult
from src.providers.errors import (
    CloudProviderAvatarUploadError,
    CloudProviderAvatarDeletionError,
    GravatarResolveError,
)
from src.utils.constants import MESSAGE_ERROR_FAILED_TO_UPLOAD_FILE_ERROR_TEMPLATE
from src.utils.logger import logger

from .dtos import UserDTO
from .errors import FileUploadFailedError
from .validators.file_validator import (
    validate_file_size,
    validate_file_extension,
    validate_file_mime_type,
    EmptyFileValidationError,
    TooLargeFileValidationError,
    UnsupportedMimeTypeValidationError,
    UnsupportedFileTypeValidationError,
)


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
        self, file: UploadFile, user: UserDTO
    ) -> AvatarUploadResult:
        """
        Upload new avatar to cloud storage and return upload metadata.

        Raises:
            UnsupportedFileTypeValidationError:
                - Raised when the file's MIME type or extension is not in the allowed types.
                - Raised when the extension is not in the allowed file extension.
            EmptyFileValidationError
                Raised when the file is empty (zero size).
            TooLargeFileValidationError:
                Raised when the file is too large.

        Do not raise:
            TooSmallFileValidationError here - small files are allowed and no check is performed.
        """
        # Validate file before upload
        try:
            validate_file_mime_type(file, app_config.AVATAR_ALLOWED_MIME_TYPES)
            validate_file_extension(file, app_config.AVATAR_ALLOWED_FILE_EXT)
            validate_file_size(file, app_config.AVATAR_MAX_FILE_SIZE)
        except UnsupportedMimeTypeValidationError as exc:
            logger.debug(
                "Avatar file MIME type is invalid (user_id=%s): %s", user.id, str(exc)
            )
            raise
        except UnsupportedFileTypeValidationError as exc:
            logger.debug(
                "Avatar file type is invalid (user_id=%s): %s", user.id, str(exc)
            )
            raise
        except EmptyFileValidationError as exc:
            logger.debug("Avatar file is empty (user_id=%s): %s", user.id, str(exc))
            raise

        except TooLargeFileValidationError as exc:
            logger.debug("Avatar file is too large (user_id=%s): %s", user.id, str(exc))
            raise

        # Upload file using provider
        try:
            return await self.cloud_provider.upload_avatar(file.file, user)
        except CloudProviderAvatarUploadError as exc:
            logger.warning(
                "Failed avatar upload attempt (filename: %s, size: %s bytes, user: %s): %s",
                file.filename,
                file.size,
                user,
                str(exc),
            )
            raise FileUploadFailedError(
                MESSAGE_ERROR_FAILED_TO_UPLOAD_FILE_ERROR_TEMPLATE.format(
                    file_type="avatar"
                )
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

    async def delete_avatar(
        self, user: UserDTO, avatar_to_delete_url: Optional[str]
    ) -> None:
        """
        Remove user's avatar from cloud storage.

        No deletion for Gravatar avatars as they are not cloud stored or managed.

        Best-effort --> Do not raise error, just log non-critical error
        """
        if GravatarProvider.is_gravatar_avatar(avatar_to_delete_url):
            # No deletion for Gravatar avatars
            logger.debug(
                "Gravatar avatar not managed by cloud detected, skipping deletion avatar for %s",
                user,
            )
            return

        try:
            await self.cloud_provider.delete_avatar(user)
        except CloudProviderAvatarDeletionError as exc:
            # best-effort:
            # Log and continue - deletion failures shouldn't break user flow
            logger.error(
                "Failed to delete avatar for user_id=%s avatar_url=%s: %s",
                user.id,
                user.avatar,
                exc,
            )
