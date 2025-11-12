"""
Application configuration module.

Loads environment variables from a `.env` file and provides a singleton
Config instance with database connection settings.
"""

import os
from pathlib import Path
import sys
from typing import List
import tomllib

from dotenv import load_dotenv

from src.utils.logger import logger

BASE_DIR = Path(__file__).parent.parent.parent

pyproject_toml_path = BASE_DIR / "pyproject.toml"

load_dotenv(BASE_DIR / ".env")  # Load variables from .env


class Config:
    """Holds configuration values for the application, such as database URLs."""

    # CORS settings
    # List of sources that are allowed to have access to the the app
    _cors_origins: str = os.getenv("CORS_ORIGINS", default="")
    CORS_ORIGINS: List[str] = (
        [origin.strip() for origin in _cors_origins.split(",")] if _cors_origins else []
    )

    # API web server settings
    WEB_PORT = int(os.getenv("WEB_PORT", default="3000"))
    DEBUG = os.getenv("DEBUG", default="False") == "True"

    # Database settings
    DB_HOST: str = os.getenv("DB_HOST", default="api-db")
    DB_PORT: int = int(os.getenv("DB_PORT", default="5432"))
    DB_NAME: str = os.getenv("DB_NAME", default="postgres")
    DB_APP_USER: str = os.getenv("DB_APP_USER", default="postgres")
    DB_APP_USER_PASSWORD: str = os.getenv("DB_APP_PASSWORD", default="")

    DB_URL: str = (
        f"postgresql+asyncpg://{DB_APP_USER}:{DB_APP_USER_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # Database admin panel settings
    DB_ADMIN_PANEL_ACCESS_EMAIL: str = os.getenv(
        "DB_ADMIN_PANEL_ACCESS_EMAIL", default="pgadmin@local.dev"
    )
    DB_ADMIN_PANEL_PASSWORD = os.getenv("DB_ADMIN_PANEL_PASSWORD", default="")
    DB_ADMIN_PANEL_PORT = int(os.getenv("DB_ADMIN_PANEL_PORT", default="5050"))

    # Auth settings
    AUTH_JWT_SECRET = os.getenv("AUTH_JWT_SECRET", default="")
    AUTH_JWT_ACCESS_EXPIRATION_SECONDS = int(
        os.getenv("AUTH_JWT_ACCESS_EXPIRATION_SECONDS", default="3600")
    )
    AUTH_JWT_REFRESH_EXPIRATION_SECONDS = int(
        os.getenv("AUTH_JWT_REFRESH_EXPIRATION_SECONDS", default="604800")
    )
    AUTH_JWT_ALGORITHM = os.getenv("AUTH_JWT_ALGORITHM", default="HS256")

    # Usernames
    SUPERADMIN_USERNAME = os.getenv("AUTH_SUPERADMIN_USERNAME", default="superadmin")

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

    @property
    def effective_reserved_usernames(self) -> set[str]:
        """Return reserved usernames excluding system admin accounts."""
        return self.RESERVED_USERNAMES - {self.SUPERADMIN_USERNAME.lower()}

    # Domain logic settings

    UPCOMING_BIRTHDAYS_PERIOD_DAYS: int = 7
    DO_MOVE_CELEBRATION_FEB_29_TO_FEB_28: bool = True

    with pyproject_toml_path.open("rb") as f:
        pyproject_data = tomllib.load(f)

    # App metadata
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

    # Version / author / license
    APP_VERSION = pyproject_data["project"].get("version", "0.0.0")
    APP_AUTHOR_NAME = pyproject_data["project"].get("authors", ["Unknown"])[0]["name"]
    APP_AUTHOR_EMAIL = pyproject_data["project"].get("authors", ["Unknown"])[0]["email"]
    APP_HOMEPAGE = pyproject_data["project"]["urls"].get("Homepage", "")
    APP_LICENSE_TITLE = (
        pyproject_data["project"]
        .get("license", "Unknown License")
        .get("text", "Unknown License")
    )
    APP_LICENSE_URL = (
        "https://github.com/oleksandr-romashko/goit-pythonweb-hw-10/blob/main/LICENSE"
    )


# === Exit on critical vars ===

# Require required values and prevent from values being default values

required_vars = [
    "DB_ADMIN_USER_PASSWORD",
    "DB_APP_USER_PASSWORD",
    "DB_ADMIN_PANEL_PASSWORD",
    "AUTH_JWT_SECRET",
]
default_values = [
    "your_db_admin_user_password_here",
    "your_db_app_user_password_here",
    "your_jwt_secret_here",
    "your_pgadmin_user_secret_password_here",
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
    return config
