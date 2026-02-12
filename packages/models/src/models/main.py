from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .inputs import CurrencyAmount

# --- Enums ---


class OpType(StrEnum):
    """
    Discriminator for operations.
    """

    STANDARD = "STANDARD"  # Uses Labor, Parts, Tools
    PURCHASE = "PURCHASE"  # Uses Currency


class NodeStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# --- Base Node ---


class BaseNode(BaseModel):
    """Common fields for every node in the tree."""

    id: UUID = Field(default_factory=uuid4)
    name: str | None = None  # Currency might not have a name? Or keep it.
    description: str | None = None


# --- Constituent Nodes ---


class PartNode(BaseNode):
    """
    An assembly or state. Can be the root of a tree.
    Children = single operation node (created_by).
    """

    status: NodeStatus = NodeStatus.PENDING


class CurrencyNode(BaseNode):
    """
    Represents a currency (e.g. USD, EUR).
    """

    iso_code: str | None = None  # e.g. "USD"


class LaborNode(BaseNode):
    """
    Represents a type of labor (e.g. 'Welding', 'Assembly').
    """

    hourly_rate: float = 0.0


class ToolNode(BaseNode):
    """
    Represents a tool instance or type.
    Must reference a PartNode that defines the tool physically.
    """

    linked_part_id: UUID
    cost_rate: float = 0.0
    rate_unit: str = "hour"


class OperationNode(BaseNode):
    """
    A procedure with a description.
    STANDARD: consumes Labor, Parts, Tools.
    PURCHASE: consumes Currency.
    """

    op_type: OpType = OpType.STANDARD
    # These estimates might be derived or direct, keeping them for now
    estimated_duration_minutes: float = 0.0
    cost_estimate: float = 0.0
    properties: dict[str, Any] = Field(default_factory=dict)


# --- Quantities (Edges/Inputs) ---


class QuantityBase(BaseModel):
    quantity: float
    unit: str  # e.g. "kg", "hours", "pieces"


class PartQuantity(QuantityBase):
    part: PartNode


class LaborQuantity(QuantityBase):
    labor: LaborNode


class ToolQuantity(QuantityBase):
    tool: ToolNode


class CurrencyQuantity(QuantityBase):
    currency: CurrencyNode


class QuantityInput(QuantityBase):
    """
    Input structure for specifying quantities by ID.
    Used for creating operations.
    """

    resource_id: UUID


__all__ = [
    "OpType",
    "NodeStatus",
    "BaseNode",
    "PartNode",
    "CurrencyNode",
    "LaborNode",
    "ToolNode",
    "OperationNode",
    "QuantityBase",
    "PartQuantity",
    "LaborQuantity",
    "ToolQuantity",
    "CurrencyQuantity",
    "QuantityInput",
    "CurrencyAmount",
]
