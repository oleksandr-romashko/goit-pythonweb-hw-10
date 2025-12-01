"""Provider module for external services."""

from .avatar_provider import GravatarProvider
from .cloud_provider import (
    AvatarUploadResult,
    CloudProvider,
    CloudinaryCloudProvider,
)
from .mail_provider import MailProvider, FastMailProvider

__all__ = [
    "AvatarUploadResult",
    "CloudProvider",
    "CloudinaryCloudProvider",
    "GravatarProvider",
    "MailProvider",
    "FastMailProvider",
]
