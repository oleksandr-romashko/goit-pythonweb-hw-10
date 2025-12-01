"""Module exposing service-level custom exceptions."""

from .providers_errors import (
    CloudAvatarDeletionError,
    CloudAvatarUploadError,
    GravatarResolveError,
)

__all__ = [
    "CloudAvatarDeletionError",
    "CloudAvatarUploadError",
    "GravatarResolveError",
]
