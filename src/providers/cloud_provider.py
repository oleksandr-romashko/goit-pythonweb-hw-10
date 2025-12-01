"""Low-level cloud storage provider using Cloudinary integration."""

from abc import ABC, abstractmethod
from typing import Optional, Union, TypedDict, BinaryIO

import anyio.to_thread
import cloudinary  # type: ignore
from cloudinary import uploader

from src.config import app_config
from src.services.dtos import UserDTO
from src.utils.logger import logger
from src.utils.security.identifiers import get_user_identifier, get_avatar_identifier

from .errors import CloudAvatarUploadError, CloudAvatarDeletionError


class AvatarUploadResult(TypedDict):
    """Typed class to represent result of file upload to the cloud"""

    url: str
    public_id: Optional[str]
    version: Optional[int]


class CloudProvider(ABC):
    """Abstract class for a cloud provider"""

    @abstractmethod
    async def upload_avatar(
        self, file: Union[BinaryIO, bytes], user: UserDTO
    ) -> AvatarUploadResult:
        """Upload avatar file to the cloud."""

    @abstractmethod
    async def delete_avatar(self, user: UserDTO) -> None:
        """Delete file from the cloud."""


class CloudinaryCloudProvider(CloudProvider):
    """
    Cloud storage provider using Cloudinary.

    Handles low-level upload/delete operations for files.
    Higher-level logic (e.g., user rules) should live in the service layer.
    """

    def __init__(
        self,
        cloud_name: str,
        api_key: str,
        api_secret: str,
    ):
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True,
        )

    AVATAR_FILENAME_PREFIX = "avatar"

    async def upload_avatar(
        self, file: Union[BinaryIO, bytes], user: UserDTO
    ) -> AvatarUploadResult:
        """Upload avatar to the cloud storage"""

        # Generate stable user-specific avatar folder path
        avatar_folder = self._generate_user_avatar_folder_path(user)
        avatar_file_name = self._generate_avatar_file_name(user)

        try:
            result = await anyio.to_thread.run_sync(
                lambda: uploader.upload(
                    file,
                    folder=avatar_folder,
                    public_id=avatar_file_name,
                    overwrite=True,
                    invalidate=True,
                    resource_type="image",
                    allowed_formats=["jpg", "png", "webp"],
                    format="jpg",
                    transformation=[
                        {
                            "width": app_config.AVATAR_IMAGE_SIZE,
                            "height": app_config.AVATAR_IMAGE_SIZE,
                            "crop": "fill",
                            "gravity": "face",
                        }
                    ],
                )
            )
        except Exception as exc:
            logger.debug(
                "Failed to upload avatar to the cloud for user %s: %s", user.id, exc
            )
            raise CloudAvatarUploadError from exc

        # Cloudinary returns the *full* public_id including folder
        cloudinary_public_id = result["public_id"]

        # Generates the URL of the uploaded transformed image (no network request, just URL)
        # based on its public ID and transformation parameters.
        src_url = cloudinary.CloudinaryImage(cloudinary_public_id).build_url(
            width=app_config.AVATAR_IMAGE_SIZE,
            height=app_config.AVATAR_IMAGE_SIZE,
            crop="fill",
            gravity="face",
            version=result.get("version"),
        )

        return AvatarUploadResult(
            url=src_url, public_id=cloudinary_public_id, version=result.get("version")
        )

    async def delete_avatar(self, user: UserDTO) -> None:
        """
        Delete the user's avatar from Cloudinary storage.

        This removes only the single avatar file ("avatar") inside the user's
        unique hashed folder. Does nothing if the file does not exist.

        Args:
            user (UserDTO): user whose avatar should be deleted.
        """
        # Regenerate user-specific avatar folder path
        avatar_folder = self._generate_user_avatar_folder_path(user)
        avatar_file_name = self._generate_avatar_file_name(user)
        public_id = f"{avatar_folder}/{avatar_file_name}"

        try:
            result = await anyio.to_thread.run_sync(
                lambda: uploader.destroy(
                    public_id, invalidate=True, resource_type="image"
                )
            )

            if result.get("result") == "ok":
                logger.debug(
                    "Removed avatar for user_id=%s from the cloud storage", user.id
                )
            elif result.get("result") == "not_found":
                logger.debug(
                    "Avatar for user_id=%s not found in the cloud storage", user.id
                )
            else:
                logger.warning("Unexpected delete result for %s: %s", public_id, result)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("Failed to delete avatar %s: %s", public_id, exc)
            raise CloudAvatarDeletionError from exc

    def _generate_user_avatar_folder_path(self, user: UserDTO) -> str:
        """Generate user avatar folder path"""
        unique_user_identifier = get_user_identifier(user)
        base_folder = app_config.AVATAR_BASE_FOLDER
        return f"{base_folder}/user_{unique_user_identifier}"

    def _generate_avatar_file_name(self, user: UserDTO) -> str:
        """Generate user avatar folder path"""
        unique_avatar_identifier = get_avatar_identifier(user)
        return f"{CloudinaryCloudProvider.AVATAR_FILENAME_PREFIX}_{unique_avatar_identifier}"
