"""
Package for all ORM models.

Includes SQLAlchemy models and association tables.
Exposes Base for metadata management and migrations.
"""

from .base import Base
from .contact import Contact
from .user import User

__all__ = ["Base", "Contact", "User"]
