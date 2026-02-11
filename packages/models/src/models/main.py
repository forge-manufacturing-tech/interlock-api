from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

# --- Enums ---


class OpType(StrEnum):
    """
    Discriminator for operations.  Keep this minimal — specific
    behaviour lives in the ``properties`` dict, not in subclasses.
    """

    STANDARD = "STANDARD"  # Generic transformation / manual step
    PURCHASE = "PURCHASE"  # Acquiring material (subsumes outsource)


class NodeStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# --- Nodes ---


class BaseNode(BaseModel):
    """Common fields for every node in the tree."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str | None = None


class PartNode(BaseNode):
    """
    A part, material, or state in the manufacturing tree.

    Currency nodes (``is_currency=True``) are the leaf inputs that
    represent money spent and do NOT require an upstream operation.
    """

    status: NodeStatus = NodeStatus.PENDING
    is_currency: bool = False


class OperationNode(BaseNode):
    """
    A single, generic operation that transforms input parts into one
    output part.

    Type-specific data (instructions, supplier info, programme number,
    etc.) is stored in the ``properties`` dict so the schema never
    needs to change when new operation flavours are introduced.

    Equipment / tooling consumed by the operation (but not destroyed)
    is tracked via the ``operation_equipment`` junction table — those
    parts are referenced for depreciation and capacity planning but
    are **not** consumed inputs.
    """

    op_type: OpType = OpType.STANDARD
    estimated_duration_minutes: float = 0.0
    cost_estimate: float = 0.0
    properties: dict[str, Any] = Field(default_factory=dict)
