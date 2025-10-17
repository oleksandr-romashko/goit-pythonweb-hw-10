"""Package with all FastAPI dependencies"""

from .auth_dependencies import (
    get_current_user_id,
    get_current_user,
    get_current_superadmin_user,
    get_current_active_user,
    get_current_active_admin_user,
)
from .db_dependencies import (
    get_db_session,
)
from .service_dependencies import (
    get_auth_service,
    get_user_service,
    get_contacts_service,
)

__all__ = [
    "get_db_session",
    "get_auth_service",
    "get_user_service",
    "get_contacts_service",
    "get_current_user_id",
    "get_current_user",
    "get_current_superadmin_user",
    "get_current_active_user",
    "get_current_active_admin_user",
]
