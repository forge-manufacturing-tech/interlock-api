"""
SQLite schema for the Interlock manufacturing tree.

Tables
------
``part_nodes``              Parts / states (incl. currency leaves).
``operation_nodes``         Generic operations (STANDARD, PURCHASE, …).
``operation_inputs``        M:N  operation → consumed input parts.
``operation_equipment``     M:N  operation → non-consumed tool/equipment parts.

Relationships
-------------
Part.created_by   →  one operation    (FK columns on ``part_nodes``)
Operation.inputs  →  many parts       (``operation_inputs`` junction)
Operation.equip   →  many parts       (``operation_equipment`` junction)

All statements use IF NOT EXISTS — safe to run on every startup.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from database.manager import DatabaseManager


_DDL: list[str] = [
    # ── Node tables ─────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS part_nodes (
        id              TEXT PRIMARY KEY,
        name            TEXT NOT NULL,
        description     TEXT,
        status          TEXT NOT NULL DEFAULT 'PENDING'
            CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
        is_currency     INTEGER NOT NULL DEFAULT 0,
        created_by_id   TEXT,
        created_by_type TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS operation_nodes (
        id                          TEXT PRIMARY KEY,
        name                        TEXT NOT NULL,
        description                 TEXT,
        op_type                     TEXT NOT NULL DEFAULT 'STANDARD',
        estimated_duration_minutes  REAL NOT NULL DEFAULT 0.0,
        cost_estimate               REAL NOT NULL DEFAULT 0.0,
        properties                  TEXT NOT NULL DEFAULT '{}'
    )
    """,
    # ── Junction tables ─────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS operation_inputs (
        operation_id  TEXT NOT NULL
            REFERENCES operation_nodes(id) ON DELETE CASCADE,
        part_id       TEXT NOT NULL
            REFERENCES part_nodes(id) ON DELETE CASCADE,
        PRIMARY KEY (operation_id, part_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS operation_equipment (
        operation_id  TEXT NOT NULL
            REFERENCES operation_nodes(id) ON DELETE CASCADE,
        part_id       TEXT NOT NULL
            REFERENCES part_nodes(id) ON DELETE CASCADE,
        PRIMARY KEY (operation_id, part_id)
    )
    """,
]


def initialize_schema(db: DatabaseManager) -> None:
    """Create all tables idempotently."""
    for stmt in _DDL:
        db.execute(stmt)
    db.commit()
