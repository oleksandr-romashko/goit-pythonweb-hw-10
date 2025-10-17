"""FastAPI service dependencies"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.services import auth_service, AuthService, UserService, ContactService

from .db_dependencies import get_db_session


def get_auth_service() -> AuthService:
    """Dependency provider for AuthService."""
    return auth_service


def get_contacts_service(
    db_session: AsyncSession = Depends(get_db_session),
) -> ContactService:
    """Dependency provider for ContactsService."""
    return ContactService(db_session)


def get_user_service(
    db_session: AsyncSession = Depends(get_db_session),
) -> UserService:
    """Dependency provider for UserService."""
    return UserService(db_session)
