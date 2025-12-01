"""Custom exception classes for provider-level logic."""


class CloudAvatarUploadError(Exception):
    """Raised when cloud provider can't upload avatar."""


class CloudAvatarDeletionError(Exception):
    """Raised when cloud provider can't delete avatar."""


class GravatarResolveError(Exception):
    """Raised when gravatar provider can't resolve avatar."""
