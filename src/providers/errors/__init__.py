"""Module exposing service-level custom exceptions."""

from .providers_errors import (
    CloudProviderError,
    CloudProviderAvatarDeletionError,
    CloudProviderAvatarUploadError,
    CloudProviderUploadError,
    CloudProviderDeletionError,
    GravatarResolveError,
)

__all__ = [
    "CloudProviderError",
    "CloudProviderAvatarDeletionError",
    "CloudProviderAvatarUploadError",
    "CloudProviderUploadError",
    "CloudProviderDeletionError",
    "GravatarResolveError",
]
