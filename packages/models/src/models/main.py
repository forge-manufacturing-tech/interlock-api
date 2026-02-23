from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import ConfigDict
from sqlalchemy import JSON, Column, ForeignKey
from sqlmodel import Field, SQLModel

from .chat import ChatMessage, ChatSession
from .inputs import CurrencyAmount

# --- Enums ---


class OpType(StrEnum):
    """
    Discriminator for operations.
    """

    STANDARD = "STANDARD"  # Uses Labor, Parts, Tools
    PURCHASE = "PURCHASE"  # Uses Currency


# --- Base Node ---


class BaseNode(SQLModel):
    """Common fields for every node in the tree."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str | None = None
    description: str | None = None


# --- Link Tables ---


class OperationInputParts(SQLModel, table=True):
    __tablename__ = "operation_input_parts"
    operation_id: UUID = Field(sa_column=Column(ForeignKey("operation_nodes.id", ondelete="CASCADE"), primary_key=True))
    part_id: UUID = Field(sa_column=Column(ForeignKey("part_nodes.id", ondelete="CASCADE"), primary_key=True))
    quantity: float = Field(default=0.0)
    unit: str = Field(default="each")


class OperationInputLabor(SQLModel, table=True):
    __tablename__ = "operation_input_labor"
    operation_id: UUID = Field(sa_column=Column(ForeignKey("operation_nodes.id", ondelete="CASCADE"), primary_key=True))
    labor_id: UUID = Field(sa_column=Column(ForeignKey("labor_nodes.id", ondelete="CASCADE"), primary_key=True))
    quantity: float = Field(default=0.0)
    unit: str = Field(default="hours")


class OperationInputTools(SQLModel, table=True):
    __tablename__ = "operation_input_tools"
    operation_id: UUID = Field(sa_column=Column(ForeignKey("operation_nodes.id", ondelete="CASCADE"), primary_key=True))
    tool_id: UUID = Field(sa_column=Column(ForeignKey("tool_nodes.id", ondelete="CASCADE"), primary_key=True))
    quantity: float = Field(default=0.0)
    unit: str = Field(default="hours")


class OperationInputCurrency(SQLModel, table=True):
    __tablename__ = "operation_input_currency"
    operation_id: UUID = Field(sa_column=Column(ForeignKey("operation_nodes.id", ondelete="CASCADE"), primary_key=True))
    currency_id: UUID = Field(sa_column=Column(ForeignKey("currency_nodes.id", ondelete="CASCADE"), primary_key=True))
    quantity: float = Field(default=0.0)
    unit: str = Field(default="units")


# --- Constituent Nodes ---


class PartNode(BaseNode, table=True):
    """
    A physical thing: raw material, sub-assembly, or finished product.
    Each part is created by exactly one operation (purchase or assembly).

    ``unit_of_measure`` defines what "1 unit" of this part means — e.g.
    "each", "kg", "meter", "liter".  This is critical for correct
    quantity calculations in BOMs and quotes.
    """

    __tablename__ = "part_nodes"

    unit_of_measure: str = Field(default="each")

    # Optional graph fields (not in original Pydantic but needed for DB/Graph)
    created_by_id: UUID | None = Field(default=None)
    created_by_type: str | None = Field(default=None)


class CurrencyNode(BaseNode, table=True):
    """
    Represents a currency (e.g. USD, EUR).
    """

    __tablename__ = "currency_nodes"

    iso_code: str | None = None  # e.g. "USD"


class LaborNode(BaseNode, table=True):
    """
    Represents a type of labor (e.g. 'Welding', 'Assembly').

    ``hourly_rate`` is the cost per hour for this labor type.
    ``skill_level`` documents the required skill or certification
    (e.g. "AWS D1.1 Certified Welder") — essential for work instructions.
    """

    __tablename__ = "labor_nodes"

    hourly_rate: float = Field(default=0.0)
    skill_level: str | None = None


class ToolNode(BaseNode, table=True):
    """
    Represents a tool or machine instance.
    Must reference a PartNode that defines the physical equipment.

    ``cost_rate`` and ``rate_unit`` describe operating cost (e.g. $50/hour).
    ``setup_time_minutes`` is the fixed time to set up the machine before
    each use — this is a separate cost bucket from run time.
    """

    __tablename__ = "tool_nodes"

    linked_part_id: UUID = Field(foreign_key="part_nodes.id")
    cost_rate: float = Field(default=0.0)
    rate_unit: str = Field(default="hour")
    setup_time_minutes: float = Field(default=0.0)


class OperationNode(BaseNode, table=True):
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

    __tablename__ = "operation_nodes"

    op_type: OpType = Field(default=OpType.STANDARD)
    instructions: str | None = None
    setup_time_minutes: float = Field(default=0.0)
    estimated_duration_minutes: float = Field(default=0.0)
    yield_rate: float = Field(default=1.0)
    cost_estimate: float = Field(default=0.0)
    properties: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    # Pydantic configuration to allow arbitrary types if needed, though dict[str, Any] is standard
    model_config = ConfigDict(arbitrary_types_allowed=True)


# --- Quantities (Edges/Inputs) ---
# These are used for API request/response models and not DB tables themselves (mostly).
# Although they mirror the link tables, the API often nests them.


class QuantityBase(SQLModel):
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
    "OperationInputParts",
    "OperationInputLabor",
    "OperationInputTools",
    "OperationInputCurrency",
    "ChatSession",
    "ChatMessage",
]
