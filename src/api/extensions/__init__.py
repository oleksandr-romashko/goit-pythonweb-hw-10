"""Package with api extensions"""

from .cors import init_cors
from .processing_time import add_processing_time_header

__all__ = ["init_cors", "add_processing_time_header"]
