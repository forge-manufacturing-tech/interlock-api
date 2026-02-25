"""
Interlock Graph — public API for the manufacturing tree.

Exposes flat CRUD functions, traversal, and tree validation.
For stateful usage, instantiate ``GraphRepository`` directly.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from database.manager import DatabaseManager
from models.chat import ChatMessage, ChatSession
from models.main import (
    BaseNode,
    FileAttachment,
    LaborNode,
    OperationNode,
    PartNode,
    PurchaseNode,
    ToolNode,
)

from orm.chat import ChatRepository
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
    "update_part",
    "delete_part",
    # Labor CRUD
    "create_labor",
    "get_labor",
    "list_labor",
    # Tool CRUD
    "create_tool",
    "list_tools",
    # Any-node lookup
    "get_node_by_id",
    # Traversal
    "get_full_timeline",
    "get_ancestors",
    "get_leaf_currencies",
    "get_tree_json",
    "get_bom",
    # File Attachments
    "add_file_attachment",
    "list_file_attachments",
    "get_file_attachment",
    "delete_file_attachment",
    # Validation
    "validate_tree",
    # Chat
    "ChatRepository",
    "create_chat_session",
    "list_chat_sessions",
    "get_chat_session",
    "add_chat_message",
    "get_chat_messages",
]


# ── Helpers ────────────────────────────────────────────────────────


_shared_db: DatabaseManager | None = None
_shared_repo: GraphRepository | None = None
_shared_chat_repo: ChatRepository | None = None


def _repo(db: DatabaseManager | None = None) -> GraphRepository:
    global _shared_db, _shared_repo
    if db is not None:
        return GraphRepository(db)
    if _shared_repo is None:
        _shared_db = DatabaseManager()
        _shared_repo = GraphRepository(_shared_db)
    return _shared_repo


# ── Atomic Transactions ────────────────────────────────────────────


def purchase_part(
    part: PartNode,
    purchase: PurchaseNode,
    db: DatabaseManager | None = None,
) -> PartNode:
    return _repo(db).purchase_part(part, purchase)


def manufacture_part(
    part: PartNode,
    operation: OperationNode,
    db: DatabaseManager | None = None,
) -> PartNode:
    return _repo(db).manufacture_part(part, operation)


# ── Part CRUD ──────────────────────────────────────────────────────


def get_part(
    part_id: UUID,
    db: DatabaseManager | None = None,
) -> PartNode | None:
    return _repo(db).get_part(part_id)


def list_parts(
    *,
    limit: int = 100,
    offset: int = 0,
    db: DatabaseManager | None = None,
) -> list[PartNode]:
    return _repo(db).list_parts(
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


def list_tools(
    db: DatabaseManager | None = None,
) -> list[ToolNode]:
    return _repo(db).list_tools()


# ── Any-node lookup ────────────────────────────────────────────────


def get_node_by_id(
    node_id: UUID,
    db: DatabaseManager | None = None,
) -> BaseNode | None:
    return _repo(db).get_node(node_id)


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
) -> list[PurchaseNode]:
    return _repo(db).get_leaf_currencies(part_id)


def get_tree_json(
    part_id: UUID,
    db: DatabaseManager | None = None,
) -> dict:
    return _repo(db).get_tree_json(part_id)


def get_bom(
    part_id: UUID,
    quantity: float = 1.0,
    db: DatabaseManager | None = None,
) -> list[dict]:
    return _repo(db).get_bom(part_id, quantity)


# ── File Attachments ──────────────────────────────────────────────


def add_file_attachment(
    name: str,
    storage_path: str,
    node_id: UUID,
    content_type: str | None = None,
    size: int | None = None,
    owner_id: UUID | None = None,
    db: DatabaseManager | None = None,
) -> FileAttachment:
    return _repo(db).add_file_attachment(
        name=name,
        storage_path=storage_path,
        node_id=node_id,
        content_type=content_type,
        size=size,
        owner_id=owner_id,
    )


def list_file_attachments(
    node_id: UUID,
    db: DatabaseManager | None = None,
) -> list[FileAttachment]:
    return _repo(db).list_file_attachments(
        node_id=node_id,
    )


def get_file_attachment(
    attachment_id: UUID,
    db: DatabaseManager | None = None,
) -> FileAttachment | None:
    return _repo(db).get_file_attachment(attachment_id)


def delete_file_attachment(
    attachment_id: UUID,
    db: DatabaseManager | None = None,
) -> bool:
    return _repo(db).delete_file_attachment(attachment_id)


# ── Validation ────────────────────────────────────────────────────


def validate_tree(
    root_id: UUID,
    db: DatabaseManager | None = None,
) -> ValidationResult:
    return _repo(db).validate_tree(root_id)


# ── Chat ──────────────────────────────────────────────────────────


def _chat_repo(db: DatabaseManager | None = None) -> ChatRepository:
    global _shared_db, _shared_chat_repo
    if db is not None:
        return ChatRepository(db)
    if _shared_chat_repo is None:
        if _shared_db is None:
            _shared_db = DatabaseManager()
        _shared_chat_repo = ChatRepository(_shared_db)
    return _shared_chat_repo


def create_chat_session(
    user_id: UUID,
    title: str | None = None,
    db: DatabaseManager | None = None,
) -> ChatSession:
    return _chat_repo(db).create_session(user_id, title)


def list_chat_sessions(
    user_id: UUID,
    db: DatabaseManager | None = None,
) -> list[ChatSession]:
    return _chat_repo(db).list_sessions(user_id)


def get_chat_session(
    session_id: UUID,
    db: DatabaseManager | None = None,
) -> ChatSession | None:
    return _chat_repo(db).get_session(session_id)


def add_chat_message(
    session_id: UUID,
    role: str,
    content: Any,
    tool_calls: Any | None = None,
    db: DatabaseManager | None = None,
) -> ChatMessage:
    return _chat_repo(db).add_message(session_id, role, content, tool_calls)


def get_chat_messages(
    session_id: UUID,
    db: DatabaseManager | None = None,
) -> list[ChatMessage]:
    return _chat_repo(db).get_messages(session_id)
