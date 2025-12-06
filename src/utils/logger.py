"""
Application-wide logging configuration.

Sets up the logger with a consistent format and provides
a reusable logger instance for the application.
"""

import logging
import os

APP_ENV = os.getenv("APP_ENV", "prod").lower()

if APP_ENV == "dev":
    LOG_LEVEL = "DEBUG"
else:
    LOG_LEVEL = "INFO"

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("Application")
