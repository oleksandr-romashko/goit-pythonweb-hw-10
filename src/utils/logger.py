"""
Application-wide logging configuration.

Sets up the logger with a consistent format and provides
a reusable logger instance for the application.
"""

import logging
import os

# Read log level from environment
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),  # default level
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("Application")
