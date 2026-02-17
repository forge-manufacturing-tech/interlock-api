# ORM Package

This package provides a high-level **Repository** pattern for interacting with the manufacturing graph.

## Responsibilities

1.  **CRUD Operations**: Create, Read, Update, Delete for all node types (Part, Operation, Labor, Tool, Currency).
2.  **Graph Traversal**: Methods like `get_full_timeline`, `get_ancestors`, and `get_leaf_currencies`.
3.  **Validation**: Ensures tree integrity (e.g., no cycles, valid inputs) via `validate_tree`.
4.  **Schema Initialization**: Automatically initializes the database schema on startup via `GraphRepository.__init__`.

## Schema Management

This package uses an **Idempotent Initialization** strategy.
- When `GraphRepository` is instantiated, it calls `database.schema.initialize_schema()`.
- This runs `CREATE TABLE IF NOT EXISTS` for all tables.
- **No Migration Tool**: There is no separate migration framework (like Alembic). Schema changes must be backward-compatible or handled manually.
