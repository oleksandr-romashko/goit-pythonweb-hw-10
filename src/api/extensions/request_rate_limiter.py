"""Application-wide request rate limiter."""

from slowapi import Limiter
from slowapi.util import get_remote_address

request_rate_limiter = Limiter(key_func=get_remote_address)
"""Slowapi rate limiter"""
