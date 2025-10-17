"""
Application configuration module.

Loads environment variables from a `.env` file and provides a singleton
Config instance with database connection settings.
"""

import os
from pathlib import Path
import tomllib

from dotenv import load_dotenv

load_dotenv()  # Load variables from .env

pyproject_toml_path = Path(__file__).parent.parent.parent / "pyproject.toml"


class Config:
    """Holds configuration values for the application, such as database URLs."""

    # Web server settings
    WEB_PORT = int(os.getenv("WEB_PORT", default="3000"))
    DEBUG = os.getenv("DEBUG", default="False") == "True"

    # Database settings
    DB_HOST: str = os.getenv("DB_HOST", default="localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", default="5432"))
    DB_NAME: str = os.getenv("DB_NAME", default="postgres")
    DB_USER: str = os.getenv("DB_USER", default="postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", default="")

    DB_URL: str = (
        f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # Auth settings
    AUTH_JWT_SECRET = os.getenv("AUTH_JWT_SECRET", default="")
    if not AUTH_JWT_SECRET:
        raise ValueError(
            "❌ AUTH_JWT_SECRET environment variable is not set. "
            "Please define it before running the application."
        )
    AUTH_JWT_EXPIRATION_SECONDS = int(
        os.getenv("AUTH_JWT_EXPIRATION_SECONDS", default="3600")
    )
    AUTH_JWT_ALGORITHM = os.getenv("AUTH_JWT_ALGORITHM", default="HS256")

    # Usernames
    SUPERADMIN_USERNAME = os.getenv("AUTH_SUPERADMIN_USERNAME", default="superadmin")
    ADMIN_USERNAME = os.getenv("AUTH_ADMIN_USERNAME", default="admin")

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
        return self.RESERVED_USERNAMES - {
            self.SUPERADMIN_USERNAME.lower(),
            self.ADMIN_USERNAME.lower(),
        }

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


config = Config()
"""Singleton instance of Config containing application settings."""


def get_app_config() -> Config:
    return config
