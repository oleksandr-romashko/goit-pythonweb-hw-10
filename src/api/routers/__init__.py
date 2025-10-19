"""Package for FastAPI routers"""

from .auth_router import router as auth_router
from .contacts_router import router as contacts_router
from .me_router import router as me_router
from .root_router import router as root_router
from .users_router import router as users_router
from .utils_router import router as utils_router

__all__ = [
    "auth_router",
    "contacts_router",
    "me_router",
    "root_router",
    "users_router",
    "utils_router",
]
