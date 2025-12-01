"""
Utilities for generating stable and privacy-safe application identifiers.

These helpers build deterministic hashed identifiers used for:
    - User-level internal identifiers
    - Avatar storage identifiers

Each identifier is derived from the user ID and an application-level salt,
ensuring stability without exposing original values.
"""

from src.config import app_config
from src.services.dtos import UserDTO
from src.utils.hash_utils import get_hash


DEFAULT_HASH_LENGTH = 12
"""
Default length of truncated SHA-256 identifiers.

12 hex characters ≈ 48 bits of entropy, providing a negligible collision
probability for practical application-scale usage.
"""


def _build_identifier(raw_value: str, length: int) -> str:
    """
    Return a truncated SHA-256 hash of the given raw value.
    Internal helper for higher-level identifier builders.
    """
    return get_hash(raw_value, length=length)


def get_user_identifier(user: UserDTO, length: int = DEFAULT_HASH_LENGTH) -> str:
    """
    Stable internal identifier for a user.

    Derived from:
        user.id + SALT_USER

    Used for:
        - Internal grouping
        - Non-sensitive stable references
    """
    raw = f"{user.id}:{app_config.SALT_USER}"
    return _build_identifier(raw, length)


def get_avatar_identifier(user: UserDTO, length: int = DEFAULT_HASH_LENGTH) -> str:
    """
    Deterministic identifier for avatar storage.

    Derived from:
        user.id + SALT_AVATAR

    Used for:
        - Avatar folder names, file names or object keys
        - Avoiding exposure of raw avatar IDs in storage systems
    """
    raw = f"{user.id}:{app_config.SALT_AVATAR}"
    return _build_identifier(raw, length)
