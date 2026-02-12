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
    CurrencyAmount,
    CurrencyNode,
    CurrencyQuantity,
    LaborNode,
    LaborQuantity,
    NodeStatus,
    OperationNode,
    OpType,
    PartNode,
    PartQuantity,
    QuantityInput,
    ToolNode,
    ToolQuantity,
)

from orm.repository import (
    GraphRepository,
    ValidationResult,
)

__all__ = [
    # Classes
    "GraphRepository",
    "ValidationResult",
    # Atomic Transactions
    "purchase_part",
    "manufacture_part",
    # Part CRUD
    "get_part",
    "list_parts",
    "list_root_parts",
    "update_part",
    "delete_part",
    # Currency CRUD
    "create_currency",
    "get_currency",
    "list_currencies",
    "delete_currency",
    # Labor CRUD
    "create_labor",
    "get_labor",
    "list_labor",
    # Tool CRUD
    "create_tool",
    "get_tool",
    "list_tools",
    # Operation CRUD
    "get_operation",
    "list_operations",
    "update_operation",
    "delete_operation",
    # Any-node lookup
    "get_node_by_id",
    # Relationships — created_by
    "get_created_by",
    "get_output_part",
    # Relationships — inputs (Parts)
    "get_input_parts",
    # Relationships — inputs (Labor)
    "get_input_labor",
    # Relationships — inputs (Tools)
    "get_input_tools",
    # Relationships — inputs (Currency)
    "get_input_currencies",
    # Traversal
    "get_full_timeline",
    "get_ancestors",
    "get_leaf_currencies",
    "get_tree_json",
    # Validation
    "validate_tree",
]


# ── Helpers ────────────────────────────────────────────────────────


def _repo(db: DatabaseManager | None = None) -> GraphRepository:
    return GraphRepository(db or DatabaseManager())


# ── Atomic Transactions ────────────────────────────────────────────


def purchase_part(
    part: PartNode,
    operation: OperationNode,
    cost: list[CurrencyAmount],
    db: DatabaseManager | None = None,
) -> PartNode:
    return _repo(db).purchase_part(part, operation, cost)


def manufacture_part(
    part: PartNode,
    operation: OperationNode,
    input_parts: list[QuantityInput],
    input_labor: list[QuantityInput],
    input_tools: list[QuantityInput],
    db: DatabaseManager | None = None,
) -> PartNode:
    return _repo(db).manufacture_part(
        part, operation, input_parts, input_labor, input_tools
    )


# ── Part CRUD ──────────────────────────────────────────────────────


def get_part(
    part_id: UUID,
    db: DatabaseManager | None = None,
) -> PartNode | None:
    return _repo(db).get_part(part_id)


def list_parts(
    *,
    status: NodeStatus | None = None,
    limit: int = 100,
    offset: int = 0,
    db: DatabaseManager | None = None,
) -> list[PartNode]:
    return _repo(db).list_parts(
        status=status,
        limit=limit,
        offset=offset,
    )


def list_root_parts(
    db: DatabaseManager | None = None,
) -> list[PartNode]:
    return _repo(db).list_root_parts()


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


# ── Currency CRUD ──────────────────────────────────────────────────


def create_currency(
    curr: CurrencyNode,
    db: DatabaseManager | None = None,
) -> CurrencyNode:
    return _repo(db).create_currency(curr)


def get_currency(
    curr_id: UUID,
    db: DatabaseManager | None = None,
) -> CurrencyNode | None:
    return _repo(db).get_currency(curr_id)


def list_currencies(
    db: DatabaseManager | None = None,
) -> list[CurrencyNode]:
    return _repo(db).list_currencies()


def delete_currency(
    curr_id: UUID,
    db: DatabaseManager | None = None,
) -> bool:
    return _repo(db).delete_currency(curr_id)


# ── Labor CRUD ─────────────────────────────────────────────────────


def create_labor(
    labor: LaborNode,
    db: DatabaseManager | None = None,
) -> LaborNode:
    return _repo(db).create_labor(labor)


def get_labor(
    labor_id: UUID,
    db: DatabaseManager | None = None,
) -> LaborNode | None:
    return _repo(db).get_labor(labor_id)


def list_labor(
    db: DatabaseManager | None = None,
) -> list[LaborNode]:
    return _repo(db).list_labor()


# ── Tool CRUD ──────────────────────────────────────────────────────


def create_tool(
    tool: ToolNode,
    db: DatabaseManager | None = None,
) -> ToolNode:
    return _repo(db).create_tool(tool)


def get_tool(
    tool_id: UUID,
    db: DatabaseManager | None = None,
) -> ToolNode | None:
    return _repo(db).get_tool(tool_id)


def list_tools(
    db: DatabaseManager | None = None,
) -> list[ToolNode]:
    return _repo(db).list_tools()


# ── Operation CRUD ─────────────────────────────────────────────────


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


# Parts
def get_input_parts(
    op_id: UUID,
    db: DatabaseManager | None = None,
) -> list[PartQuantity]:
    return _repo(db).get_input_parts(op_id)


# Labor
def get_input_labor(
    op_id: UUID,
    db: DatabaseManager | None = None,
) -> list[LaborQuantity]:
    return _repo(db).get_input_labor(op_id)


# Tools
def get_input_tools(
    op_id: UUID,
    db: DatabaseManager | None = None,
) -> list[ToolQuantity]:
    return _repo(db).get_input_tools(op_id)


# Currency
def get_input_currencies(
    op_id: UUID,
    db: DatabaseManager | None = None,
) -> list[CurrencyQuantity]:
    return _repo(db).get_input_currencies(op_id)


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
) -> list[CurrencyNode]:
    return _repo(db).get_leaf_currencies(part_id)


def get_tree_json(
    part_id: UUID,
    db: DatabaseManager | None = None,
) -> dict:
    return _repo(db).get_tree_json(part_id)


# ── Validation ────────────────────────────────────────────────────


def validate_tree(
    root_id: UUID,
    db: DatabaseManager | None = None,
) -> ValidationResult:
    return _repo(db).validate_tree(root_id)
