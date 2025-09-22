"""
Application configuration module.

Loads environment variables from a `.env` file and provides a singleton
Config instance with database connection settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env


class Config:
    """Holds configuration values for the application, such as database URLs."""

    WEB_PORT = int(os.getenv("WEB_PORT", "3000"))
    DEBUG = os.getenv("DEBUG", "False") == "True"

    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "postgres")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    DB_URL: str = (
        f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    UPCOMING_BIRTHDAYS_PERIOD_DAYS: int = 7
    DO_MOVE_CELEBRATION_FEB_29_TO_FEB_28: bool = True


config = Config()
"""Singleton instance of Config containing application settings."""
