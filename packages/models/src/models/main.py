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
    name: str | None = None
    description: str | None = None


# --- Constituent Nodes ---


class PartNode(BaseNode):
    """
    A physical thing: raw material, sub-assembly, or finished product.
    Each part is created by exactly one operation (purchase or assembly).

    ``unit_of_measure`` defines what "1 unit" of this part means — e.g.
    "each", "kg", "meter", "liter".  This is critical for correct
    quantity calculations in BOMs and quotes.
    """

    status: NodeStatus = NodeStatus.PENDING
    unit_of_measure: str = "each"


class CurrencyNode(BaseNode):
    """
    Represents a currency (e.g. USD, EUR).
    """

    iso_code: str | None = None  # e.g. "USD"


class LaborNode(BaseNode):
    """
    Represents a type of labor (e.g. 'Welding', 'Assembly').

    ``hourly_rate`` is the cost per hour for this labor type.
    ``skill_level`` documents the required skill or certification
    (e.g. "AWS D1.1 Certified Welder") — essential for work instructions.
    """

    hourly_rate: float = 0.0
    skill_level: str | None = None


class ToolNode(BaseNode):
    """
    Represents a tool or machine instance.
    Must reference a PartNode that defines the physical equipment.

    ``cost_rate`` and ``rate_unit`` describe operating cost (e.g. $50/hour).
    ``setup_time_minutes`` is the fixed time to set up the machine before
    each use — this is a separate cost bucket from run time.
    """

    linked_part_id: UUID
    cost_rate: float = 0.0
    rate_unit: str = "hour"
    setup_time_minutes: float = 0.0


class OperationNode(BaseNode):
    """
    A manufacturing procedure.

    STANDARD: consumes Parts + Labor + Tools → produces one Part.
    PURCHASE: consumes Currency → produces one Part.

    Fields for work instructions & quoting:
    - ``instructions``:  Step-by-step work instruction text.
    - ``setup_time_minutes``:  Fixed setup time (independent of quantity).
    - ``estimated_duration_minutes``:  Run time per unit produced.
    - ``yield_rate``:  Fraction of good output (0.95 = 5% scrap).
                       To produce N good units you need N / yield_rate of input.
    - ``cost_estimate``:  Optional override / estimate for the total op cost.
    - ``properties``:  Freeform key-value bag for any extra parameters
                       (temperatures, tolerances, pressures, etc.).
    """

    op_type: OpType = OpType.STANDARD
    instructions: str | None = None
    setup_time_minutes: float = 0.0
    estimated_duration_minutes: float = 0.0
    yield_rate: float = 1.0
    cost_estimate: float = 0.0
    properties: dict[str, Any] = Field(default_factory=dict)


# --- Quantities (Edges/Inputs) ---


class QuantityBase(BaseModel):
    quantity: float
    unit: str  # e.g. "kg", "hours", "each"


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
