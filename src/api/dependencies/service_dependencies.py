"""FastAPI service dependencies"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.providers.cache_providers.contact_cache import ContactRedisCacheProvider
from src.providers.cache_providers.contacts_count_cache import (
    ContactsCountUserRedisCacheProvider,
)
from src.providers.cache_providers.user_cache import UserRedisCacheProvider
from src.services import (
    AuthService,
    auth_service,
    FileService,
    ContactService,
    MailService,
    mail_service,
    UserService,
)

from .db_dependencies import get_db_session
from .provider_dependencies import (
    get_contact_cache_provider,
    get_contacts_count_cache_provider,
    get_cloud_provider,
    get_gravatar_provider,
    get_user_cache_provider,
)

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
    contact_cache: ContactRedisCacheProvider = Depends(get_contact_cache_provider),
    contacts_count_cache: ContactsCountUserRedisCacheProvider = Depends(
        get_contacts_count_cache_provider
    ),
) -> ContactService:
    """Dependency provider for ContactsService."""
    return ContactService(
        db_session,
        contact_cache=contact_cache,
        contacts_count_cache=contacts_count_cache,
    )


def get_user_service(
    db_session: AsyncSession = Depends(get_db_session),
    user_cache: UserRedisCacheProvider = Depends(get_user_cache_provider),
) -> UserService:
    """Dependency provider for UserService."""
    return UserService(db_session, user_cache=user_cache)
