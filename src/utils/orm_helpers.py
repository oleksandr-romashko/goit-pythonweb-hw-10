"""Helper functions for working with SQLAlchemy ORM objects."""

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import inspect


def contact_to_dict(obj: DeclarativeBase) -> dict:
    """
    Convert a SQLAlchemy ORM object into a dictionary containing only column attributes.

    Args:
        obj (DeclarativeBase): Any SQLAlchemy ORM model instance.

    Returns:
        dict: Dictionary mapping column names to their values.
    """
    data = {o.key: getattr(obj, o.key) for o in inspect(obj).mapper.column_attrs}
    return data
