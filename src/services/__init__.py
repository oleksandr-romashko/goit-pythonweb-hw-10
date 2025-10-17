"""Main services module providing access to all service classes and instances."""

from .auth_service import auth_service, AuthService
from .contact_service import ContactService
from .user_service import UserService

__all__ = [
    "auth_service",
    "AuthService",
    "ContactService",
    "UserService",
]
