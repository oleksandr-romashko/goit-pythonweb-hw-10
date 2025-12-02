"""Custom exception classes for provider-level logic."""


class CloudProviderError(Exception):
    """General error for cloud provider."""


class CloudProviderUploadError(CloudProviderError):
    """Low-level cloud provider upload error."""


class CloudProviderAvatarUploadError(CloudProviderUploadError):
    """Raised when cloud provider can't upload avatar."""


class CloudProviderDeletionError(CloudProviderError):
    """Low-level cloud provider delete error."""


class CloudProviderAvatarDeletionError(CloudProviderDeletionError):
    """Raised when cloud provider can't delete avatar."""


class GravatarResolveError(Exception):
    """Raised when gravatar provider can't resolve avatar."""
