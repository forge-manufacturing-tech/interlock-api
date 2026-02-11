"""
Interlock Graph — public API for the manufacturing tree.

Exposes flat CRUD functions, traversal, and tree validation.
For stateful usage, instantiate ``GraphRepository`` directly.
"""

from __future__ import annotations

from uuid import UUID

from database.manager import DatabaseManager
from models.main import (
    BaseNode,
    NodeStatus,
    OperationNode,
    OpType,
    PartNode,
)

from interlock_graph.repository import (
    GraphRepository,
    ValidationResult,
)

__all__ = [
    # Classes
    "GraphRepository",
    "ValidationResult",
    # Part CRUD
    "create_part",
    "get_part",
    "list_parts",
    "update_part",
    "delete_part",
    # Operation CRUD
    "create_operation",
    "get_operation",
    "list_operations",
    "update_operation",
    "delete_operation",
    # Any-node lookup
    "get_node_by_id",
    # Relationships — created_by
    "set_created_by",
    "clear_created_by",
    "get_created_by",
    "get_output_part",
    # Relationships — inputs
    "add_input",
    "remove_input",
    "get_inputs",
    "get_consumers",
    # Relationships — equipment
    "add_equipment",
    "remove_equipment",
    "get_equipment",
    # Traversal
    "get_full_timeline",
    "get_ancestors",
    "get_leaf_currencies",
    # Validation
    "validate_tree",
]


# ── Helpers ────────────────────────────────────────────────────────


def _repo(db: DatabaseManager | None = None) -> GraphRepository:
    return GraphRepository(db or DatabaseManager())


# ── Part CRUD ──────────────────────────────────────────────────────


def create_part(
    part: PartNode,
    db: DatabaseManager | None = None,
) -> PartNode:
    return _repo(db).create_part(part)


def get_part(
    part_id: UUID,
    db: DatabaseManager | None = None,
) -> PartNode | None:
    return _repo(db).get_part(part_id)


def list_parts(
    *,
    status: NodeStatus | None = None,
    is_currency: bool | None = None,
    limit: int = 100,
    offset: int = 0,
    db: DatabaseManager | None = None,
) -> list[PartNode]:
    return _repo(db).list_parts(
        status=status,
        is_currency=is_currency,
        limit=limit,
        offset=offset,
    )


def update_part(
    part: PartNode,
    db: DatabaseManager | None = None,
) -> PartNode:
    return _repo(db).update_part(part)


def delete_part(
    part_id: UUID,
    db: DatabaseManager | None = None,
) -> bool:
    return _repo(db).delete_part(part_id)


# ── Operation CRUD ─────────────────────────────────────────────────


def create_operation(
    op: OperationNode,
    db: DatabaseManager | None = None,
) -> OperationNode:
    return _repo(db).create_operation(op)


def get_operation(
    op_id: UUID,
    db: DatabaseManager | None = None,
) -> OperationNode | None:
    return _repo(db).get_operation(op_id)


def list_operations(
    *,
    op_type: OpType | None = None,
    limit: int = 100,
    offset: int = 0,
    db: DatabaseManager | None = None,
) -> list[OperationNode]:
    return _repo(db).list_operations(op_type=op_type, limit=limit, offset=offset)


def update_operation(
    op: OperationNode,
    db: DatabaseManager | None = None,
) -> OperationNode:
    return _repo(db).update_operation(op)


def delete_operation(
    op_id: UUID,
    db: DatabaseManager | None = None,
) -> bool:
    return _repo(db).delete_operation(op_id)


# ── Any-node lookup ────────────────────────────────────────────────


def get_node_by_id(
    node_id: UUID,
    db: DatabaseManager | None = None,
) -> BaseNode | None:
    return _repo(db).get_node(node_id)


# ── Relationships: created_by ──────────────────────────────────────


def set_created_by(
    part_id: UUID,
    op_id: UUID,
    db: DatabaseManager | None = None,
) -> None:
    _repo(db).set_created_by(part_id, op_id)


def clear_created_by(
    part_id: UUID,
    db: DatabaseManager | None = None,
) -> None:
    _repo(db).clear_created_by(part_id)


def get_created_by(
    part_id: UUID,
    db: DatabaseManager | None = None,
) -> OperationNode | None:
    return _repo(db).get_created_by(part_id)


def get_output_part(
    op_id: UUID,
    db: DatabaseManager | None = None,
) -> PartNode | None:
    return _repo(db).get_output_part(op_id)


# ── Relationships: inputs ─────────────────────────────────────────


def add_input(
    op_id: UUID,
    part_id: UUID,
    db: DatabaseManager | None = None,
) -> None:
    _repo(db).add_input(op_id, part_id)


def remove_input(
    op_id: UUID,
    part_id: UUID,
    db: DatabaseManager | None = None,
) -> bool:
    return _repo(db).remove_input(op_id, part_id)


def get_inputs(
    op_id: UUID,
    db: DatabaseManager | None = None,
) -> list[PartNode]:
    return _repo(db).get_inputs(op_id)


def get_consumers(
    part_id: UUID,
    db: DatabaseManager | None = None,
) -> list[OperationNode]:
    return _repo(db).get_consumers(part_id)


# ── Relationships: equipment ──────────────────────────────────────


def add_equipment(
    op_id: UUID,
    part_id: UUID,
    db: DatabaseManager | None = None,
) -> None:
    _repo(db).add_equipment(op_id, part_id)


def remove_equipment(
    op_id: UUID,
    part_id: UUID,
    db: DatabaseManager | None = None,
) -> bool:
    return _repo(db).remove_equipment(op_id, part_id)


def get_equipment(
    op_id: UUID,
    db: DatabaseManager | None = None,
) -> list[PartNode]:
    return _repo(db).get_equipment(op_id)


# ── Traversal ─────────────────────────────────────────────────────


def get_full_timeline(
    part_id: UUID,
    db: DatabaseManager | None = None,
) -> list[BaseNode]:
    return _repo(db).get_full_timeline(part_id)


def get_ancestors(
    part_id: UUID,
    db: DatabaseManager | None = None,
) -> list[PartNode]:
    return _repo(db).get_ancestors(part_id)


def get_leaf_currencies(
    part_id: UUID,
    db: DatabaseManager | None = None,
) -> list[PartNode]:
    return _repo(db).get_leaf_currencies(part_id)


# ── Validation ────────────────────────────────────────────────────


def validate_tree(
    root_id: UUID,
    db: DatabaseManager | None = None,
) -> ValidationResult:
    return _repo(db).validate_tree(root_id)
