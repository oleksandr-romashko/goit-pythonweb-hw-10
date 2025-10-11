"""
Utilities for hashing and verifying passwords.

Provides functions to generate a secure password hash and verify a plain password
against a stored hash.
"""

import bcrypt


def get_password_hash(password: str) -> str:
    """
    Hash a plain-text password.

    Args:
        password (str): The plain-text password to hash.

    Returns:
        str: The hashed password as a UTF-8 string.
    """
    hashed_password = bcrypt.hashpw(password.encode(encoding="utf-8"), bcrypt.gensalt())
    return hashed_password.decode(encoding="utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a hash.

    Args:
        plain_password (str): The plain-text password to verify.
        hashed_password (str): The previously hashed password.

    Returns:
        bool: True if the password matches the hash, False otherwise.
    """
    return bcrypt.checkpw(
        password=plain_password.encode("utf-8"),
        hashed_password=hashed_password.encode("utf-8"),
    )
