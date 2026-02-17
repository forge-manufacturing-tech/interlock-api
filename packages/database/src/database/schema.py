"""
[DEPRECATED]
This file contained the raw SQL schema initialization.
We have moved to using Alembic migrations with SQLAlchemy models.

See:
- packages/database/src/database/sql_models.py (SQLAlchemy models)
- packages/database/alembic/ (Migration scripts)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from database.manager import DatabaseManager


def initialize_schema(db: DatabaseManager) -> None:
    """
    [DEPRECATED]
    Schema initialization is now handled by Alembic.
    This function is kept for backward compatibility but does nothing.
    """
    pass
