"""FastAPI dependencies for db layer"""

from src.db import session_manager


async def get_db_session():
    """FastAPI dependency to provide an async single-use database session."""
    async with session_manager.session() as session:
        yield session
