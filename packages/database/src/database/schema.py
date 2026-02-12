"""
SQLite schema for the Interlock manufacturing tree.

Tables
------
Nodes:
- ``part_nodes``:        Assemblies / States.
- ``currency_nodes``:    Currencies (USD, EUR).
- ``labor_nodes``:       Labor types.
- ``tool_nodes``:        Tool instances (links to physical PartNode).
- ``operation_nodes``:   Procedures (STANDARD or PURCHASE).

Relationships (Edges):
- Part.created_by -> Operation (1:1, via FK on part_nodes)
- Operation Inputs (M:N with Quantity/Unit):
    - ``operation_input_parts``
    - ``operation_input_labor``
    - ``operation_input_tools``
    - ``operation_input_currency`` (for PURCHASE ops)
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
        created_by_id   TEXT,
        created_by_type TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS currency_nodes (
        id              TEXT PRIMARY KEY,
        name            TEXT NOT NULL,
        description     TEXT,
        iso_code        TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS labor_nodes (
        id              TEXT PRIMARY KEY,
        name            TEXT NOT NULL,
        description     TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tool_nodes (
        id              TEXT PRIMARY KEY,
        name            TEXT NOT NULL,
        description     TEXT,
        linked_part_id  TEXT NOT NULL
            REFERENCES part_nodes(id)
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
    # ── Input tables (Edges) ────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS operation_input_parts (
        operation_id    TEXT NOT NULL
            REFERENCES operation_nodes(id) ON DELETE CASCADE,
        part_id         TEXT NOT NULL
            REFERENCES part_nodes(id) ON DELETE CASCADE,
        quantity        REAL NOT NULL DEFAULT 0.0,
        unit            TEXT NOT NULL DEFAULT 'pcs',
        PRIMARY KEY (operation_id, part_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS operation_input_labor (
        operation_id    TEXT NOT NULL
            REFERENCES operation_nodes(id) ON DELETE CASCADE,
        labor_id        TEXT NOT NULL
            REFERENCES labor_nodes(id) ON DELETE CASCADE,
        quantity        REAL NOT NULL DEFAULT 0.0,
        unit            TEXT NOT NULL DEFAULT 'hours',
        PRIMARY KEY (operation_id, labor_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS operation_input_tools (
        operation_id    TEXT NOT NULL
            REFERENCES operation_nodes(id) ON DELETE CASCADE,
        tool_id         TEXT NOT NULL
            REFERENCES tool_nodes(id) ON DELETE CASCADE,
        quantity        REAL NOT NULL DEFAULT 0.0,
        unit            TEXT NOT NULL DEFAULT 'pcs',
        PRIMARY KEY (operation_id, tool_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS operation_input_currency (
        operation_id    TEXT NOT NULL
            REFERENCES operation_nodes(id) ON DELETE CASCADE,
        currency_id     TEXT NOT NULL
            REFERENCES currency_nodes(id) ON DELETE CASCADE,
        quantity        REAL NOT NULL DEFAULT 0.0,
        unit            TEXT NOT NULL DEFAULT 'units',
        PRIMARY KEY (operation_id, currency_id)
    )
    """,
]


def initialize_schema(db: DatabaseManager) -> None:
    """Create all tables idempotently."""
    for stmt in _DDL:
        db.execute(stmt)
    db.commit()
