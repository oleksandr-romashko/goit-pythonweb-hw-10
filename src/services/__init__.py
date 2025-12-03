"""Main services module providing access to all service classes and instances."""

from .auth_service import auth_service, AuthService, AuthTokenType
from .file_service import FileService
from .contact_service import ContactService
from .mail_service import MailService, mail_service
from .markers import NOT_PROVIDED
from .user_service import UserService

__all__ = [
    "NOT_PROVIDED",
    "auth_service",
    "AuthService",
    "AuthTokenType",
    "ContactService",
    "FileService",
    "MailService",
    "mail_service",
    "UserService",
]
