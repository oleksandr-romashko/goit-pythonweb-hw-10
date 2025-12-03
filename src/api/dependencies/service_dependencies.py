"""FastAPI service dependencies"""

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.services import (
    AuthService,
    auth_service,
    FileService,
    ContactService,
    MailService,
    mail_service,
    UserService,
)

from .cache_dependencies import get_app_cache
from .db_dependencies import get_db_session
from .provider_dependencies import get_cloud_provider, get_gravatar_provider

# ---------- Singleton services (stateless) ----------


def get_auth_service() -> AuthService:
    """Dependency provider for AuthService."""
    return auth_service


def get_file_service() -> FileService:
    """Dependency provider for FileService."""
    return FileService(get_cloud_provider(), get_gravatar_provider())


def get_mail_service() -> MailService:
    """Dependency provider for EmailService."""
    return mail_service


# ---------- Request-scoped services (stateful) ----------


def get_contacts_service(
    db_session: AsyncSession = Depends(get_db_session),
) -> ContactService:
    """Dependency provider for ContactsService."""
    return ContactService(db_session)


def get_user_service(
    db_session: AsyncSession = Depends(get_db_session),
    cache: Redis = Depends(get_app_cache),
) -> UserService:
    """Dependency provider for UserService."""
    return UserService(db_session, cache=cache)
