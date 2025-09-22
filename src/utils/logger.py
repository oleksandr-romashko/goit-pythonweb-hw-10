"""
Application-wide logging configuration.

Sets up the logger with a consistent format and provides
a reusable logger instance for the application.
"""

import logging

logging.basicConfig(
    level=logging.INFO,  # default level
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("Application")
