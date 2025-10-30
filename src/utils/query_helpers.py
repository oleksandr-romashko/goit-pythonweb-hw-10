"""Helper functions for query operations."""

from typing import Dict, Tuple


def get_pagination(pagination: Dict[str, int]) -> Tuple[int, int]:
    """Extract skip and limit as a tuple from pagination dict with defaults."""
    return pagination.get("skip", 0), pagination.get("limit", 50)
