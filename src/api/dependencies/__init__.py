"""Package with all FastAPI dependencies"""

from .auth_dependencies import (
    Require,
    get_current_user_factory,
    get_current_user,
    get_current_active_user,
    get_current_active_moderator_user,
    get_current_active_admin_user,
    get_current_superadmin_user,
)
from .db_dependencies import (
    get_db_session,
)
from .service_dependencies import (
    get_auth_service,
    get_contacts_service,
    get_file_service,
    get_mail_service,
    get_user_service,
)
from .token_dependencies import get_current_user_id

__all__ = [
    "Require",
    "get_auth_service",
    "get_contacts_service",
    "get_current_user_factory",
    "get_current_user",
    "get_current_user_id",
    "get_current_active_user",
    "get_current_active_moderator_user",
    "get_current_active_admin_user",
    "get_current_superadmin_user",
    "get_db_session",
    "get_file_service",
    "get_mail_service",
    "get_user_service",
]
