"""
Utility module providing hashing helpers based on SHA-256.

This module offers a simple, deterministic hashing function used across the
application wherever a stable and reproducible hash value is required.
"""

import hashlib
from typing import Optional


def get_hash(input_str: str, length: Optional[int] = None) -> str:
    """
    Generate a deterministic SHA-256 hash for the given string.

    The function always returns the same output for the same input, regardless
    of environment, runtime, or number of executions.

    Args:
        input_str (str): The input string to hash.
        length (Optional[int]): If provided, limits the result to the first
            `length` characters of the hex digest.

    Returns:
        str: Hexadecimal SHA-256 hash, full or truncated.

    Examples:
        >>> get_hash("123")
        'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3'

        >>> get_hash("123", length=12)
        'a665a4592042'
    """
    digest = hashlib.sha256(input_str.encode()).hexdigest()
    return digest[:length] if length else digest
