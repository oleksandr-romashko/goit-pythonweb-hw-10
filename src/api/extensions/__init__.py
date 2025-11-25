"""Package with api extensions"""

from .cors import init_cors
from .processing_time import add_processing_time_header
from .rate_limiter import init_rate_limiter, close_rate_limiter

__all__ = [
    "init_cors",
    "add_processing_time_header",
    "init_rate_limiter",
    "close_rate_limiter",
]
