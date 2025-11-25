"""Cache package exposing cache connection and related utilities."""

from .connection import get_redis

__all__ = ["get_redis"]
