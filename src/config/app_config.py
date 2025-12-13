"""
Application configuration module.

Loads environment variables from a `.env` file and provides a singleton
Config instance with database connection settings.
"""

import os
from pathlib import Path
import sys
import tomllib
from typing import List, Dict

from dotenv import load_dotenv
from pydantic import SecretStr

from src.utils.logger import logger
from src.utils.constants import (
    DEFAULT_AUTH_JWT_SECRET,
    DEFAULT_CACHE_PASSWORD,
    DEFAULT_DB_ADMIN_USER_PASSWORD,
    DEFAULT_DB_ADMIN_PANEL_ACCESS_EMAIL,
    DEFAULT_DB_APP_USER_PASSWORD,
    DEFAULT_MAIL_JWT_SECRET,
    DEFAULT_MAIL_USERNAME,
    DEFAULT_MAIL_PASSWORD,
    DEFAULT_MAIL_FROM,
    DEFAULT_DB_ADMIN_PANEL_PASSWORD,
    DEFAULT_CLOUDINARY_NAME,
    DEFAULT_CLOUDINARY_API_KEY,
    DEFAULT_CLOUDINARY_API_SECRET,
    DEFAULT_SALT_USER,
    DEFAULT_SALT_AVATAR,
)

BASE_DIR = Path(__file__).parent.parent.parent  # Root project directory

pyproject_toml_path = BASE_DIR / "pyproject.toml"

load_dotenv(BASE_DIR / ".env")  # Load variables from .env


# TODO: Refactor to from pydantic_settings import BaseSettings and Settings(BaseSettings) class
class Config:
    """Holds configuration values for the application, such as database URLs."""

    # ==========================
    # Environment settings
    # ==========================

    APP_ENV = os.getenv("APP_ENV", "prod").lower()
    DEV_ENV = APP_ENV == "dev"

    # ==========================
    # Application settings
    # ==========================

    # === App metadata ===

    with pyproject_toml_path.open("rb") as f:
        pyproject_data = tomllib.load(f)

    APP_TITLE = "Contacts Manager API"
    APP_DESCRIPTION = (
        "### REST API for storing and managing personal contacts\n"
        "This API provides functionality for **storing and managing personal contacts** "
        "for individual users and includes **role-based access control** "
        "(_[RBAC](https://wikipedia.org/wiki/Role-based_access_control)_) "
        "for convenient API management.\n<br><br>"
        "\n---\n"
        "#### 🔐 **Authentication & Authorization**\n"
        "- Authentication is implemented using an _OAuth2-compatible password-based flow_ "
        "that issues limited-life "
        "_[JWT access tokens](https://wikipedia.org/wiki/JSON_Web_Token)_.\n"
        "- Tokens are obtained via the _[/api/auth/oauth2-login](/api/auth/oauth2-login)_ endpoint "
        "using a username and password.\n"
        "- Most endpoints require a valid Bearer token in the Authorization header.\n"
        "#### 👤 **User Roles & Permissions**\n"
        "- New regular users can register themselves and manage only their own contacts.\n"
        "- Admin and Superadmin users have extended permissions (e.g., user management).\n"
        "- The system is initially seeded with a Superadmin account configured "
        "via environment variables.<br>\n\n"
        "#### 📇 **Contacts Management**\n"
        "- Authenticated users can manage (_create_, _read_, _update_, and _delete_) "
        "their contacts using this API.\n"
        "- Admin users may have additional visibility and control depending on configuration.<br>\n"
        "#### 🧰 **Tech Notes**\n"
        "- All endpoints return JSON responses.\n"
        "- Interactive documentation is available via Swagger UI (_[/docs](/docs)_) "
        "and ReDoc (_[/redoc](/redoc)_).\n"
        "<br><br>"
        "\n---\n"
    )

    # Version / author / contacts

    APP_VERSION = pyproject_data["project"].get("version", "0.0.0")
    APP_AUTHOR_NAME = pyproject_data["project"].get("authors", ["Unknown"])[0]["name"]
    APP_AUTHOR_EMAIL = pyproject_data["project"].get("authors", ["Unknown"])[0]["email"]
    APP_HOMEPAGE = pyproject_data["project"]["urls"].get("Homepage", "")
    APP_CONTACT = {
        "name": APP_AUTHOR_NAME,
        "url": APP_HOMEPAGE,
        "email": APP_AUTHOR_EMAIL,
    }

    # License

    APP_LICENSE_TITLE = (
        pyproject_data["project"]
        .get("license", "Unknown License")
        .get("text", "Unknown License")
    )
    APP_LICENSE_URL = (
        "https://github.com/oleksandr-romashko/goit-pythonweb-hw-10/blob/main/LICENSE"
    )
    APP_LICENSE_INFO: Dict = {
        "name": f"{APP_LICENSE_TITLE} License",
        "url": APP_LICENSE_URL,
    }

    # === API & docs web server settings ===

    WEB_PORT = int(os.getenv("WEB_PORT", default="8000"))
    STATIC_DIR = "static"
    EMAIL_VERIFICATION_REDIRECT_URL = os.getenv(
        "EMAIL_VERIFICATION_REDIRECT_URL", default=""
    ).strip()

    # === CORS settings ===

    # List of sources that are allowed to have access to the the app (user protection in browser)
    _cors_origins: str = os.getenv("CORS_ORIGINS", default="")
    CORS_ORIGINS: List[str] = (
        [origin.strip() for origin in _cors_origins.split(",")] if _cors_origins else []
    )

    # === Auth settings ===

    AUTH_JWT_SECRET = os.getenv("AUTH_JWT_SECRET", default="")
    AUTH_JWT_ACCESS_EXPIRATION_SECONDS = int(
        os.getenv("AUTH_JWT_ACCESS_EXPIRATION_SECONDS", default="3600")
    )
    AUTH_JWT_REFRESH_EXPIRATION_SECONDS = int(
        os.getenv("AUTH_JWT_REFRESH_EXPIRATION_SECONDS", default="604800")
    )
    AUTH_JWT_ALGORITHM = os.getenv("AUTH_JWT_ALGORITHM", default="HS256")

    # === Domain logic settings ===

    # Users

    # Default admin user
    SUPERADMIN_USERNAME = os.getenv("SUPERADMIN_USERNAME", default="superadmin")

    # Usernames - Not allowed (reserved) usernames
    RESERVED_USERNAMES: set[str] = {
        "admin",
        "administrator",
        "superadmin",
        "superuser",
        "root",
        "system",
        "moderator",
        "user",
        "test",
        "support",
    }

    # Identifiers
    SALT_USER = os.getenv("USER_IDENTIFIER_SALT", default="")
    SALT_AVATAR = os.getenv("AVATAR_IDENTIFIER_SALT", default="")

    # Celebrations logic

    UPCOMING_BIRTHDAYS_PERIOD_DAYS: int = 7
    DO_MOVE_CELEBRATION_FEB_29_TO_FEB_28: bool = True

    @property
    def effective_reserved_usernames(self) -> set[str]:
        """Return reserved usernames excluding system admin accounts."""
        return self.RESERVED_USERNAMES - {self.SUPERADMIN_USERNAME.lower()}

    # === Avatar settings ===

    AVATAR_ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
    AVATAR_ALLOWED_FILE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
    AVATAR_MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB

    AVATAR_IMAGE_SIZE: int = 250
    AVATAR_BASE_FOLDER = "contacts_manager_api/images/avatars"

    # === Email settings ===

    MAIL_JWT_SECRET = os.getenv("MAIL_JWT_SECRET", default="")
    MAIL_JWT_CONFIRMATION_EXPIRATION_SECONDS = int(
        os.getenv("MAIL_JWT_EXPIRATION_SECONDS", default="604800")
    )
    MAIL_SERVER = os.getenv("MAIL_SERVER", default="smtp.meta.ua")
    MAIL_PORT = os.getenv("MAIL_PORT", default="465")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", default="")
    MAIL_PASSWORD = SecretStr(os.getenv("MAIL_PASSWORD", default=""))
    MAIL_FROM = os.getenv("MAIL_FROM", default=MAIL_USERNAME)
    MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", default="Rest API Service")
    template_dir: Path = Path(BASE_DIR / "src" / "templates").resolve()

    # === Cloud storage settings ===

    CLD_NAME = os.getenv("CLOUDINARY_NAME", default="")
    CLD_API_KEY = os.getenv("CLOUDINARY_API_KEY", default="")
    CLD_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", default="")
    CLD_URL = f"cloudinary://{CLD_API_KEY}:{CLD_API_SECRET}@{CLD_NAME}"

    # ==========================
    # Cache settings
    # ==========================

    CACHE_HOST: str = os.getenv("CACHE_HOST", default="cache-redis")
    CACHE_PORT: int = int(os.getenv("CACHE_PORT", default="6379"))
    CACHE_PASSWORD: str = os.getenv("CACHE_PASSWORD", default="")
    CACHE_URL_BASE: str = f"redis://:{CACHE_PASSWORD}@{CACHE_HOST}:{CACHE_PORT}"
    CACHE_USER_TTL: int = 60
    CACHE_CONTACTS_COUNT_TTL: int = 60

    # ==========================
    # Database settings
    # ==========================

    DB_HOST: str = os.getenv("DB_HOST", default="api-db")
    DB_PORT: int = int(os.getenv("DB_PORT", default="5432"))
    DB_NAME: str = os.getenv("DB_NAME", default="postgres")
    DB_APP_USER: str = os.getenv("DB_APP_USER", default="postgres")
    DB_APP_USER_PASSWORD: str = os.getenv("DB_APP_USER_PASSWORD", default="")

    DB_URL: str = (
        f"postgresql+asyncpg://{DB_APP_USER}:{DB_APP_USER_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # ==========================
    # Database admin panel settings
    # ==========================

    DB_ADMIN_PANEL_ACCESS_EMAIL: str = os.getenv(
        "DB_ADMIN_PANEL_ACCESS_EMAIL", default=DEFAULT_DB_ADMIN_PANEL_ACCESS_EMAIL
    )
    DB_ADMIN_PANEL_PASSWORD = os.getenv("DB_ADMIN_PANEL_PASSWORD", default="")
    DB_ADMIN_PANEL_PORT = int(os.getenv("DB_ADMIN_PANEL_PORT", default="5050"))


# ==================================================
# Exit on critical vars and warn on value defaults
# ==================================================
#
# (Require required values and prevent from values being default values)

required_vars = [
    "AUTH_JWT_SECRET",
    "CACHE_PASSWORD",
    "DB_ADMIN_USER",
    "DB_ADMIN_USER_PASSWORD",
    "DB_APP_USER_PASSWORD",
    "DB_ADMIN_PANEL_PASSWORD",
    "MAIL_JWT_SECRET",
    "MAIL_USERNAME",
    "MAIL_PASSWORD",
    "CLOUDINARY_NAME",
    "CLOUDINARY_API_KEY",
    "CLOUDINARY_API_SECRET",
]
default_values = [
    DEFAULT_AUTH_JWT_SECRET,
    DEFAULT_CACHE_PASSWORD,
    DEFAULT_DB_ADMIN_USER_PASSWORD,
    DEFAULT_DB_APP_USER_PASSWORD,
    DEFAULT_MAIL_JWT_SECRET,
    DEFAULT_MAIL_USERNAME,
    DEFAULT_MAIL_PASSWORD,
    DEFAULT_MAIL_FROM,
    DEFAULT_DB_ADMIN_PANEL_PASSWORD,
    DEFAULT_CLOUDINARY_NAME,
    DEFAULT_CLOUDINARY_API_KEY,
    DEFAULT_CLOUDINARY_API_SECRET,
    DEFAULT_SALT_USER,
    DEFAULT_SALT_AVATAR,
]
errors = []
for var in required_vars:
    value = os.environ.get(var)
    if not value:
        errors.append(f"App config error: {var} is not set.")
    if value in default_values:
        errors.append(
            f"App config error: {var} value can't be default, please change it."
        )
if errors:
    for err in errors:
        logger.critical(err)
    sys.exit(1)

config = Config()
"""Singleton instance of Config containing application settings."""


def get_app_config() -> Config:
    """Get app-wide application configuration with environment values"""
    return config
