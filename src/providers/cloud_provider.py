"""Low-level cloud storage provider using Cloudinary integration."""

from abc import ABC, abstractmethod
from typing import Optional, Union, List, Dict, TypedDict, BinaryIO

import anyio.to_thread
import cloudinary  # type: ignore
from cloudinary import uploader as cloudinary_uploader

from src.config import app_config
from src.services.dtos import UserDTO
from src.utils.logger import logger
from src.utils.security.identifiers import get_user_identifier, get_avatar_identifier

from .errors import (
    CloudProviderAvatarDeletionError,
    CloudProviderAvatarUploadError,
    CloudProviderDeletionError,
    CloudProviderUploadError,
)


class AvatarUploadResult(TypedDict):
    """Typed class to represent result of file upload to the cloud"""

    url: str
    public_id: Optional[str]
    version: Optional[int]


class CloudProvider(ABC):
    """Abstract interface for a cloud provider"""

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

    AVATAR_FILENAME_PREFIX = "avatar"

    def __init__(
        self,
        cloud_name: str,
        api_key: str,
        api_secret: str,
    ):
        self.__cloudinary_auth: Dict = {
            "cloud_name": cloud_name,
            "api_key": api_key,
            "api_secret": api_secret,
        }
        cloudinary.config(secure=True, **self.__cloudinary_auth)

    # ----------------------------
    # Required by abstract base class
    # ----------------------------

    async def upload_avatar(
        self, file: Union[BinaryIO, bytes], user: UserDTO
    ) -> AvatarUploadResult:
        """
        Upload a user's avatar to Cloudinary.

        This is a high-level method responsible for:
        - building deterministic folder + filename for the user
        - applying avatar-specific transformations (resize, face crop, format)
        - delegating the actual upload to the internal `_upload_file()` helper
        - converting low-level upload response into a domain-level result object

        Args:
            file:
                A file-like object or raw bytes representing the avatar image
                to upload. Accepted formats depend on Cloudinary configuration,
                but the provider enforces ["jpg", "png", "webp"] by default.

            user:
                UserDTO for whom the avatar is being uploaded. Used only to
                generate stable and secure identifiers:
                    - folder path:  e.g. "avatars/user_<hash>"
                    - file name:    e.g. "avatar_<hash>"

        Returns:
            AvatarUploadResult:
                A TypedDict containing:
                    - url (str):
                        Public URL of the transformed avatar (auto-generated
                        from Cloudinary public_id + version).
                    - public_id (str):
                        Full Cloudinary public ID including folder.
                        Example: "avatars/user_abc123/avatar_xyz789"
                    - version (int | None):
                        Cloudinary version used for cache invalidation.
                        May be None if Cloudinary did not return a version.

        Raises:
            CloudAvatarUploadError:
                Raised when Cloudinary upload fails for any reason.
                The method logs a debug message with user.id and re-raises
                the domain-specific exception. The underlying low-level method
                `_upload_file()` raises CloudProviderUploadError, which is then
                wrapped here into CloudAvatarUploadError.
        """

        # Generate stable user-specific avatar folder path
        avatar_folder = self._build_user_avatar_folder_path(user)
        avatar_file_name = self._build_avatar_file_name(user)

        # Upload avatar
        try:
            result = await self._upload_file(
                file,
                folder=avatar_folder,
                public_id=avatar_file_name,
                display_name="avatar",
                overwrite=True,
                invalidate=True,
                resource_type="image",
                allowed_formats=["jpg", "png", "webp"],
                format="jpg",
                transformation={
                    "width": app_config.AVATAR_IMAGE_SIZE,
                    "height": app_config.AVATAR_IMAGE_SIZE,
                    "crop": "fill",
                    "gravity": "face",
                },
            )
        except CloudProviderUploadError as exc:
            logger.debug(
                "Failed to upload avatar for user_id=%s: %s", user.id, repr(exc)
            )
            raise CloudProviderAvatarUploadError from exc

        # Get the Cloudinary full public_id including folder
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
            url=src_url,
            public_id=cloudinary_public_id,
            version=result.get("version"),
        )

    async def delete_avatar(self, user: UserDTO) -> None:
        """
        Delete user's avatar from Cloudinary.

        This is a high-level method responsible for:
        - Determining the user's avatar folder and deterministic public_id.
        - Delegating actual deletion to the internal `_delete_file()` method.
        - Interpreting Cloudinary's delete result and logging meaningful messages.

        Args:
            user: UserDTO whose avatar should be deleted.

        Returns:
            None

        Raises:
            CloudProviderAvatarDeletionError:
                Raised when Cloudinary deletion fails for any reason.
                Low-level failures originate from `_delete_file()`, which raises
                `CloudProviderDeletionError`. This method catches the exception,
                logs context, and rethrows a domain-level error
                `CloudProviderAvatarDeletionError`.
        """

        # Regenerate user-specific avatar folder path and public_id
        avatar_folder = self._build_user_avatar_folder_path(user)
        avatar_file_name = self._build_avatar_file_name(user)
        public_id = f"{avatar_folder}/{avatar_file_name}"

        try:
            result = await self._delete_file(
                public_id, invalidate=True, resource_type="image"
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
        except CloudProviderDeletionError as exc:
            logger.debug(
                "Failed to delete avatar for user_id=%s, public_id=%s: %s",
                user.id,
                public_id,
                exc,
            )
            raise CloudProviderAvatarDeletionError from exc

    # ----------------------------
    # Internal low-level helpers
    # ----------------------------

    async def _upload_file(
        self,
        file: Union[BinaryIO, bytes],
        public_id: str,
        folder: Optional[str] = None,
        display_name: Optional[str] = None,
        resource_type: str = "image",
        allowed_formats: Optional[List[str]] = None,
        overwrite: bool = False,
        invalidate: bool = True,
        format: Optional[str] = None,
        transformation: Optional[Union[Dict, List[Dict]]] = None,
    ) -> Dict:
        """
        Low-level Cloudinary upload wrapper.

        This method exposes Cloudinary's native upload parameters. It should be used
        only inside provider-level code. Higher-level logic must be implemented inside
        other provider method.

        Args:
            file: The asset to upload - a file-like object or raw bytes to upload.
            public_id: The final Cloudinary public ID (without extension).
            folder: Optional Cloudinary folder path.
            display_name: Friendly name shown in the Media Library.
            resource_type: Cloudinary resource type ("image", "raw", "video"). Default="image".
                Defaults to "image" if not provided.
            allowed_formats: Optional list of allowed file extensions (e.g., ["jpg", "png"]).
                Defaults to ["jpg", "png", "webp"] if not provided.
            overwrite: Whether Cloudinary should overwrite existing asset.
                Defaults to False if not provided.
            invalidate: Invalidate cached CDN versions after upload.
                Defaults to True if not provided.
            format: Force-convert output asset to specific format (e.g. "jpg").
            transformation: One or more Cloudinary transformations to apply.

        Returns:
            dict: The Cloudinary upload response, typically containing:
                - public_id
                - secure_url
                - version
                - resource_type
                - bytes
                - width, height
                - etc.

        Raises:
            CloudProviderUploadError:
                If Cloudinary's upload operation fails. Higher-level methods
                are expected to catch it and rethrow domain-specific exceptions.
        """
        try:
            return await anyio.to_thread.run_sync(
                lambda: cloudinary_uploader.upload(
                    file,
                    public_id=public_id,
                    folder=folder,
                    display_name=display_name,
                    resource_type=resource_type,
                    allowed_formats=allowed_formats or ["jpg", "png", "webp"],
                    overwrite=overwrite,
                    invalidate=invalidate,
                    format=format,
                    transformation=transformation,
                )
            )
        except Exception as exc:
            raise CloudProviderUploadError from exc

    async def _delete_file(
        self,
        public_id: str,
        invalidate: bool = True,
        resource_type: Optional[str] = None,
    ) -> Dict:
        """
        Low-level Cloudinary delete operation.

        This method provides a thin async wrapper around
        `cloudinary.uploader.destroy()` and should only be used by
        provider-internal high-level methods.

        Args:
            public_id: The Cloudinary public_id of the resource to delete.
            invalidate:
                Whether Cloudinary should invalidate cached versions on CDN.
            resource_type:
                Cloudinary resource type (e.g. "image", "video").
                If None — Cloudinary defaults will be used.

        Returns:
            dict:
                The raw Cloudinary deletion response, usually containing:
                - result: "ok" | "not_found" | <other statuses>

        Raises:
            CloudProviderDeletionError:
                If Cloudinary fails to delete the resource or an unexpected
                exception occurs inside the SDK.
        """
        try:
            return await anyio.to_thread.run_sync(
                lambda: cloudinary_uploader.destroy(
                    public_id, invalidate=invalidate, resource_type=resource_type
                )
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            raise CloudProviderDeletionError from exc

    # ----------------------------
    # Internal utilities
    # ----------------------------

    def _build_user_avatar_folder_path(self, user: UserDTO) -> str:
        """Generate user avatar folder path"""
        unique_user_identifier = get_user_identifier(user)
        base_folder = app_config.AVATAR_BASE_FOLDER
        return f"{base_folder}/user_{unique_user_identifier}"

    def _build_avatar_file_name(self, user: UserDTO) -> str:
        """Generate user avatar folder path"""
        unique_avatar_identifier = get_avatar_identifier(user)
        return f"{CloudinaryCloudProvider.AVATAR_FILENAME_PREFIX}_{unique_avatar_identifier}"
