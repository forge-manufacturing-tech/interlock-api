"""
CRUD, traversal, and validation for the Interlock manufacturing tree.

Tree invariants
---------------
* Root is a ``PartNode``.
* Every Part must have exactly one ``created_by`` operation.
* Operations are either STANDARD or PURCHASE.
* STANDARD operations:
  - Must consume at least one Part.
  - Must use at least one Labor or Tool (parts don't assemble themselves).
  - Must NOT have Currency inputs.
  - Must have a valid yield_rate in (0, 1].
* PURCHASE operations:
  - Must consume Currency only.
  - Must NOT have Part, Labor, or Tool inputs.
* All input quantities must be positive.
* No cycles allowed.
* One-way pointers only: part → created_by, operation → inputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from database.manager import DatabaseManager
from database.schema import initialize_schema
from models.main import (
    BaseNode,
    CurrencyAmount,
    CurrencyNode,
    CurrencyQuantity,
    LaborNode,
    LaborQuantity,
    NodeShare,
    OperationInputCurrency,
    OperationInputLabor,
    OperationInputParts,
    OperationInputTools,
    OperationNode,
    OpType,
    PartNode,
    PartQuantity,
    QuantityInput,
    ToolNode,
    ToolQuantity,
)
from sqlmodel import col, delete, select

# ── Validation data classes ────────────────────────────────────────


@dataclass
class ValidationError:
    node_id: UUID
    message: str


@dataclass
class ValidationResult:
    valid: bool
    errors: list[ValidationError] = field(default_factory=list)


# ── Repository ─────────────────────────────────────────────────────


class GraphRepository:
    """Full CRUD, traversal, and validation for the tree."""

    _schema_initialized = False

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db
        if not GraphRepository._schema_initialized:
            initialize_schema(db)
            GraphRepository._schema_initialized = True

    # ===============================================================
    # Atomic Transactions (Strict Tree Construction)
    # ===============================================================

    def purchase_part(
        self,
        part: PartNode,
        operation: OperationNode,
        cost: list[CurrencyAmount],
    ) -> PartNode:
        """
        Atomically create a Part, a Purchase Operation, and link them
        with Currency inputs.
        """
        if operation.op_type != OpType.PURCHASE:
            raise ValueError("Operation must be of type PURCHASE")
        if not cost:
            raise ValueError("Purchase operation must have at least one cost")
        for c in cost:
            if c.amount <= 0:
                raise ValueError(f"Cost amount must be positive, got {c.amount}")

        with self.db.session as session:
            try:
                # 1. Link Part -> Operation
                part.created_by_id = operation.id
                part.created_by_type = operation.op_type.value

                # 2. Add Nodes
                session.add(part)
                session.add(operation)
                session.flush()

                # 3. Create Currency Nodes and Link
                for c_input in cost:
                    curr_node = CurrencyNode(
                        id=uuid4(),
                        name=f"Cost: {part.name}",
                        iso_code=c_input.currency_code,
                        description=f"Purchase cost for {part.name}",
                        owner_id=part.owner_id,
                        is_public=part.is_public,
                        project_label=part.project_label,
                    )
                    session.add(curr_node)

                    link = OperationInputCurrency(
                        operation_id=operation.id,
                        currency_id=curr_node.id,
                        quantity=c_input.amount,
                        unit=c_input.currency_code,
                    )
                    session.add(link)

                session.commit()
                session.refresh(part)
                return part
            except Exception:
                session.rollback()
                raise

    def manufacture_part(
        self,
        part: PartNode,
        operation: OperationNode,
        input_parts: list[QuantityInput],
        input_labor: list[QuantityInput],
        input_tools: list[QuantityInput],
    ) -> PartNode:
        """
        Atomically create a Part, a Standard Operation, and link inputs.
        Requires all input parts/labor/tools to exist.
        """
        if operation.op_type != OpType.STANDARD:
            raise ValueError("Operation must be of type STANDARD")

        # --- Structural validation ---
        if not input_parts:
            raise ValueError("Standard operation must have at least one input part.")
        if not (input_labor or input_tools):
            raise ValueError("Standard operation must have at least one labor or tool.")

        # --- Yield rate validation ---
        if not (0 < operation.yield_rate <= 1.0):
            raise ValueError(f"yield_rate must be in (0, 1.0], got {operation.yield_rate}")

        # --- Quantity validation ---
        for p_input in input_parts + input_labor + input_tools:
            if p_input.quantity <= 0:
                raise ValueError(f"Input quantity must be positive, got {p_input.quantity}")

        with self.db.session as session:
            try:
                # --- Existence validation ---
                for p_input in input_parts:
                    existing = session.get(PartNode, p_input.resource_id)
                    if not existing:
                        raise ValueError(f"Input Part ID {p_input.resource_id} NOT FOUND.")
                    if not existing.created_by_id:
                        raise ValueError(f"Input Part '{existing.name}' is invalid (orphaned).")
                    if existing.id == part.id:
                        raise ValueError(f"A part cannot be an input to its own creation: {part.name}")

                for l_input in input_labor:
                    if not session.get(LaborNode, l_input.resource_id):
                        raise ValueError(f"Labor {l_input.resource_id} not found")

                for t_input in input_tools:
                    if not session.get(ToolNode, t_input.resource_id):
                        raise ValueError(f"Tool {t_input.resource_id} not found")

                # 1. Link Part -> Operation
                part.created_by_id = operation.id
                part.created_by_type = operation.op_type.value

                # 2. Add Nodes
                session.add(part)
                session.add(operation)
                session.flush()

                # 3. Link Inputs
                for p_input in input_parts:
                    session.add(
                        OperationInputParts(
                            operation_id=operation.id,
                            part_id=p_input.resource_id,
                            quantity=p_input.quantity,
                            unit=p_input.unit,
                        )
                    )
                for l_input in input_labor:
                    session.add(
                        OperationInputLabor(
                            operation_id=operation.id,
                            labor_id=l_input.resource_id,
                            quantity=l_input.quantity,
                            unit=l_input.unit,
                        )
                    )
                for t_input in input_tools:
                    session.add(
                        OperationInputTools(
                            operation_id=operation.id,
                            tool_id=t_input.resource_id,
                            quantity=t_input.quantity,
                            unit=t_input.unit,
                        )
                    )

                session.commit()
                session.refresh(part)
                return part
            except Exception:
                session.rollback()
                raise

    # ===============================================================
    # CRUD Operations
    # ===============================================================

    def has_access(self, user_id: UUID | None, node: BaseNode, session: Session) -> bool:
        """Check if a user has access to a node. Must be called within an active session."""
        if node.is_public:
            return True
        if user_id is None:
            return False
        if node.owner_id == user_id:
            return True
        share = session.exec(select(NodeShare).where(NodeShare.node_id == node.id, NodeShare.user_id == user_id)).first()
        return share is not None

    def get_part(self, part_id: UUID, user_id: UUID | None = None) -> PartNode | None:
        with self.db.session as session:
            node = session.get(PartNode, part_id)
            if node and not self.has_access(user_id, node, session):
                return None
            return node

    def list_parts(self, *, limit: int = 100, offset: int = 0, user_id: UUID | None = None) -> list[PartNode]:
        with self.db.session as session:
            statement = select(PartNode).order_by(PartNode.name).limit(limit).offset(offset)
            if user_id:
                shares = select(NodeShare.node_id).where(NodeShare.user_id == user_id)
                statement = statement.where((col(PartNode.owner_id) == user_id) | (col(PartNode.is_public)) | (col(PartNode.id).in_(shares)))
            return list(session.exec(statement).all())

    def list_root_parts(self, user_id: UUID | None = None) -> list[PartNode]:
        """Find parts that are not used as inputs to any operation."""
        with self.db.session as session:
            # Parts in operation_input_parts
            used_in_ops = select(OperationInputParts.part_id)
            # Parts linked to tools that are in operation_input_tools
            used_as_tools = select(ToolNode.linked_part_id).join(OperationInputTools, col(ToolNode.id) == col(OperationInputTools.tool_id)).where(col(ToolNode.linked_part_id).is_not(None))

            statement = select(PartNode).where(col(PartNode.id).not_in(used_in_ops)).where(col(PartNode.id).not_in(used_as_tools)).order_by(PartNode.name)
            if user_id:
                shares = select(NodeShare.node_id).where(NodeShare.user_id == user_id)
                statement = statement.where((col(PartNode.owner_id) == user_id) | (col(PartNode.is_public)) | (col(PartNode.id).in_(shares)))
            return list(session.exec(statement).all())

    def update_part(self, part: PartNode) -> PartNode:
        with self.db.session as session:
            existing = session.get(PartNode, part.id)
            if not existing:
                raise ValueError(f"Part {part.id} not found")
            existing.name = part.name
            existing.description = part.description
            existing.unit_of_measure = part.unit_of_measure
            existing.owner_id = part.owner_id
            existing.is_public = part.is_public
            existing.project_label = part.project_label
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return existing

    def delete_part(self, part_id: UUID) -> bool:
        with self.db.session as session:
            part = session.get(PartNode, part_id)
            if not part:
                return False
            # Delete all linked tools first
            linked_tools = session.exec(select(ToolNode).where(ToolNode.linked_part_id == part_id)).all()
            for tool in linked_tools:
                session.delete(tool)
            session.flush()  # Ensure tools are deleted before deleting part
            session.delete(part)
            session.commit()
            return True

    # --- Currency ---

    def create_currency(self, curr: CurrencyNode) -> CurrencyNode:
        with self.db.session as session:
            session.add(curr)
            session.commit()
            session.refresh(curr)
            return curr

    def get_currency(self, curr_id: UUID, user_id: UUID | None = None) -> CurrencyNode | None:
        with self.db.session as session:
            node = session.get(CurrencyNode, curr_id)
            if node and not self.has_access(user_id, node, session):
                return None
            return node

    def list_currencies(self, user_id: UUID | None = None) -> list[CurrencyNode]:
        with self.db.session as session:
            statement = select(CurrencyNode).order_by(CurrencyNode.name)
            if user_id:
                shares = select(NodeShare.node_id).where(NodeShare.user_id == user_id)
                statement = statement.where((col(CurrencyNode.owner_id) == user_id) | (col(CurrencyNode.is_public)) | (col(CurrencyNode.id).in_(shares)))
            return list(session.exec(statement).all())

    def delete_currency(self, curr_id: UUID) -> bool:
        with self.db.session as session:
            curr = session.get(CurrencyNode, curr_id)
            if not curr:
                return False
            session.delete(curr)
            session.commit()
            return True

    # --- Labor ---

    def create_labor(self, labor: LaborNode) -> LaborNode:
        if labor.hourly_rate < 0:
            raise ValueError("hourly_rate must be non-negative")
        with self.db.session as session:
            session.add(labor)
            session.commit()
            session.refresh(labor)
            return labor

    def get_labor(self, labor_id: UUID, user_id: UUID | None = None) -> LaborNode | None:
        with self.db.session as session:
            node = session.get(LaborNode, labor_id)
            if node and not self.has_access(user_id, node, session):
                return None
            return node

    def list_labor(self, user_id: UUID | None = None) -> list[LaborNode]:
        with self.db.session as session:
            statement = select(LaborNode).order_by(LaborNode.name)
            if user_id:
                shares = select(NodeShare.node_id).where(NodeShare.user_id == user_id)
                statement = statement.where((col(LaborNode.owner_id) == user_id) | (col(LaborNode.is_public)) | (col(LaborNode.id).in_(shares)))
            return list(session.exec(statement).all())

    # --- Tools ---

    def create_tool(self, tool: ToolNode) -> ToolNode:
        if tool.cost_rate < 0:
            raise ValueError("cost_rate must be non-negative")
        with self.db.session as session:
            linked_part = session.get(PartNode, tool.linked_part_id)
            if not linked_part:
                raise ValueError(f"Linked Part {tool.linked_part_id} not found")
            if not linked_part.created_by_id:
                raise ValueError(f"Linked Part {linked_part.name} is invalid (orphaned)")

            session.add(tool)
            session.commit()
            session.refresh(tool)
            return tool

    def get_tool(self, tool_id: UUID, user_id: UUID | None = None) -> ToolNode | None:
        with self.db.session as session:
            node = session.get(ToolNode, tool_id)
            if node and not self.has_access(user_id, node, session):
                return None
            return node

    def list_tools(self, user_id: UUID | None = None) -> list[ToolNode]:
        with self.db.session as session:
            statement = select(ToolNode).order_by(ToolNode.name)
            if user_id:
                shares = select(NodeShare.node_id).where(NodeShare.user_id == user_id)
                statement = statement.where((col(ToolNode.owner_id) == user_id) | (col(ToolNode.is_public)) | (col(ToolNode.id).in_(shares)))
            return list(session.exec(statement).all())

    # --- Operations ---

    def get_operation(self, op_id: UUID, user_id: UUID | None = None) -> OperationNode | None:
        with self.db.session as session:
            node = session.get(OperationNode, op_id)
            if node and not self.has_access(user_id, node, session):
                return None
            return node

    def list_operations(self, *, op_type: OpType | None = None, limit: int = 100, offset: int = 0, user_id: UUID | None = None) -> list[OperationNode]:
        with self.db.session as session:
            statement = select(OperationNode).order_by(OperationNode.name).limit(limit).offset(offset)
            if op_type:
                statement = statement.where(OperationNode.op_type == op_type)
            if user_id:
                shares = select(NodeShare.node_id).where(NodeShare.user_id == user_id)
                statement = statement.where((col(OperationNode.owner_id) == user_id) | (col(OperationNode.is_public)) | (col(OperationNode.id).in_(shares)))
            return list(session.exec(statement).all())

    def update_operation(self, op: OperationNode) -> OperationNode:
        with self.db.session as session:
            existing = session.get(OperationNode, op.id)
            if not existing:
                raise ValueError(f"Operation {op.id} not found")

            # Update fields
            for key, value in op.model_dump(exclude={"id"}).items():
                setattr(existing, key, value)

            session.add(existing)
            session.commit()
            session.refresh(existing)
            return existing

    def delete_operation(self, op_id: UUID) -> bool:
        with self.db.session as session:
            op = session.get(OperationNode, op_id)
            if not op:
                return False
            session.delete(op)
            session.commit()
            return True

    def get_node(self, node_id: UUID, user_id: UUID | None = None) -> BaseNode | None:
        """Look up any node by ID."""
        with self.db.session as session:
            for model in [PartNode, OperationNode, CurrencyNode, LaborNode, ToolNode]:
                node = session.get(model, node_id)
                if node:
                    if not self.has_access(user_id, node, session):
                        return None
                    return node
            return None

    # ===============================================================
    # Relationships (part <-> operation)
    # ===============================================================

    def clear_created_by(self, part_id: UUID) -> None:
        with self.db.session as session:
            part = session.get(PartNode, part_id)
            if part:
                part.created_by_id = None
                part.created_by_type = None
                session.add(part)
                session.commit()

    def get_created_by(self, part_id: UUID) -> OperationNode | None:
        with self.db.session as session:
            part = session.get(PartNode, part_id)
            if not part or not part.created_by_id:
                return None
            return session.get(OperationNode, part.created_by_id)

    def get_output_part(self, op_id: UUID) -> PartNode | None:
        with self.db.session as session:
            statement = select(PartNode).where(PartNode.created_by_id == op_id)
            return session.exec(statement).first()

    # ===============================================================
    # Operation Inputs (Quantities)
    # ===============================================================

    def get_input_parts(self, op_id: UUID) -> list[PartQuantity]:
        with self.db.session as session:
            statement = select(PartNode, OperationInputParts.quantity, OperationInputParts.unit).join(OperationInputParts, col(PartNode.id) == col(OperationInputParts.part_id)).where(OperationInputParts.operation_id == op_id)
            return [PartQuantity(part=part, quantity=qty, unit=unit) for part, qty, unit in session.exec(statement)]

    def get_input_labor(self, op_id: UUID) -> list[LaborQuantity]:
        with self.db.session as session:
            statement = select(LaborNode, OperationInputLabor.quantity, OperationInputLabor.unit).join(OperationInputLabor, col(LaborNode.id) == col(OperationInputLabor.labor_id)).where(OperationInputLabor.operation_id == op_id)
            return [LaborQuantity(labor=labor, quantity=qty, unit=unit) for labor, qty, unit in session.exec(statement)]

    def get_input_tools(self, op_id: UUID) -> list[ToolQuantity]:
        with self.db.session as session:
            statement = select(ToolNode, OperationInputTools.quantity, OperationInputTools.unit).join(OperationInputTools, col(ToolNode.id) == col(OperationInputTools.tool_id)).where(OperationInputTools.operation_id == op_id)
            return [ToolQuantity(tool=tool, quantity=qty, unit=unit) for tool, qty, unit in session.exec(statement)]

    def get_input_currencies(self, op_id: UUID) -> list[CurrencyQuantity]:
        with self.db.session as session:
            statement = select(CurrencyNode, OperationInputCurrency.quantity, OperationInputCurrency.unit).join(OperationInputCurrency, col(CurrencyNode.id) == col(OperationInputCurrency.currency_id)).where(OperationInputCurrency.operation_id == op_id)
            return [CurrencyQuantity(currency=curr, quantity=qty, unit=unit) for curr, qty, unit in session.exec(statement)]

    # ===============================================================
    # Traversal (Material Flow)
    # ===============================================================

    def get_full_timeline(self, part_id: UUID, user_id: UUID | None = None) -> list[BaseNode]:
        """BFS walk from *part_id* upward (inputs) through the tree."""
        with self.db.session as session:
            start = session.get(PartNode, part_id)
            if start is None or not self.has_access(user_id, start, session):
                return []

            visited: set[UUID] = set()
            timeline: list[BaseNode] = []
            queue: list[BaseNode] = [start]

            while queue:
                node = queue.pop(0)
                if node.id in visited:
                    continue
                if not self.has_access(user_id, node, session):
                    continue
                visited.add(node.id)
                timeline.append(node)

                if isinstance(node, PartNode):
                    if node.created_by_id:
                        op = session.get(OperationNode, node.created_by_id)
                        if op:
                            queue.append(op)
                elif isinstance(node, OperationNode):
                    if node.op_type == OpType.PURCHASE:
                        # Follow Currency
                        curr_qs = select(CurrencyNode).join(OperationInputCurrency, col(CurrencyNode.id) == col(OperationInputCurrency.currency_id)).where(OperationInputCurrency.operation_id == node.id)
                        for curr in session.exec(curr_qs):
                            queue.append(curr)
                    else:
                        # Standard Op -> Parts
                        part_qs = select(PartNode).join(OperationInputParts, col(PartNode.id) == col(OperationInputParts.part_id)).where(OperationInputParts.operation_id == node.id)
                        for p in session.exec(part_qs):
                            queue.append(p)

            return timeline

    def get_ancestors(self, part_id: UUID, user_id: UUID | None = None) -> list[PartNode]:
        """All upstream parts feeding into *part_id*."""
        return [n for n in self.get_full_timeline(part_id, user_id=user_id) if isinstance(n, PartNode) and n.id != part_id]

    def get_leaf_currencies(self, part_id: UUID, user_id: UUID | None = None) -> list[CurrencyNode]:
        """Currency leaves reachable from *part_id*."""
        return [n for n in self.get_full_timeline(part_id, user_id=user_id) if isinstance(n, CurrencyNode)]

    def get_tree_json(self, part_id: UUID, user_id: UUID | None = None) -> dict:
        """Recursive tree structure for visualization."""
        with self.db.session as session:
            return self._get_tree_json_internal(part_id, user_id, session)

    def _get_tree_json_internal(self, part_id: UUID, user_id: UUID | None, session: Session) -> dict:
        """Internal recursive implementation that shares a session."""
        part = session.get(PartNode, part_id)
        if not part:
            return {}

        if not self.has_access(user_id, part, session):
                return {
                    "id": str(part.id),
                    "name": "Private Part",
                    "type": "part",
                    "description": "You do not have permission to view this part.",
                    "children": [],
                }

            res = {
                "id": str(part.id),
                "name": part.name,
                "type": "part",
                "description": part.description,
                "unit_of_measure": part.unit_of_measure,
                "children": [],
            }

            total_unit_cost = 0.0
            if part.created_by_id:
                op = session.get(OperationNode, part.created_by_id)
                if op:
                    op_node = {
                        "id": str(op.id),
                        "name": op.name,
                        "type": "operation",
                        "op_type": op.op_type.value,
                        "yield_rate": op.yield_rate,
                        "setup_time_minutes": op.setup_time_minutes,
                        "estimated_duration_minutes": op.estimated_duration_minutes,
                        "instructions": op.instructions,
                        "children": [],
                    }
                    res["children"].append(op_node)

                    # 1. Input Parts (Recursive cost)
                    part_inputs = select(PartNode, OperationInputParts.quantity, OperationInputParts.unit).join(OperationInputParts, col(PartNode.id) == col(OperationInputParts.part_id)).where(OperationInputParts.operation_id == op.id)
                    for p_node, qty, unit in session.exec(part_inputs):
                        child_tree = self._get_tree_json_internal(p_node.id, user_id, session)
                        child_cost = child_tree.get("unit_cost", 0.0)
                        total_unit_cost += qty * child_cost

                        child_tree["quantity"] = qty
                        child_tree["unit"] = unit
                        op_node["children"].append(child_tree)

                    # 2. Input Currencies
                    curr_inputs = select(CurrencyNode, OperationInputCurrency.quantity, OperationInputCurrency.unit).join(OperationInputCurrency, col(CurrencyNode.id) == col(OperationInputCurrency.currency_id)).where(OperationInputCurrency.operation_id == op.id)
                    for c_node, qty, unit in session.exec(curr_inputs):
                        total_unit_cost += qty
                        op_node["children"].append({"id": str(c_node.id), "name": c_node.name, "type": "currency", "iso_code": c_node.iso_code, "quantity": qty, "unit": unit})

                    # 3. Input Labor
                    labor_inputs = select(LaborNode, OperationInputLabor.quantity, OperationInputLabor.unit).join(OperationInputLabor, col(LaborNode.id) == col(OperationInputLabor.labor_id)).where(OperationInputLabor.operation_id == op.id)
                    for l_node, qty, unit in session.exec(labor_inputs):
                        cost = qty * l_node.hourly_rate
                        total_unit_cost += cost
                        op_node["children"].append({"id": str(l_node.id), "name": l_node.name, "type": "labor", "quantity": qty, "unit": unit, "hourly_rate": l_node.hourly_rate, "cost": cost})

                    # 4. Input Tools
                    tool_inputs = select(ToolNode, OperationInputTools.quantity, OperationInputTools.unit).join(OperationInputTools, col(ToolNode.id) == col(OperationInputTools.tool_id)).where(OperationInputTools.operation_id == op.id)
                    for t_node, qty, unit in session.exec(tool_inputs):
                        cost = qty * t_node.cost_rate
                        total_unit_cost += cost
                        tool_entry = {"id": str(t_node.id), "name": t_node.name, "type": "tool", "quantity": qty, "unit": unit, "cost_rate": t_node.cost_rate, "rate_unit": t_node.rate_unit, "cost": cost}
                        if t_node.linked_part_id:
                            tool_entry["linked_part"] = self._get_tree_json_internal(t_node.linked_part_id, user_id, session)
                        op_node["children"].append(tool_entry)

            res["unit_cost"] = total_unit_cost
            return res

    def get_bom(self, part_id: UUID, quantity: float = 1.0, user_id: UUID | None = None) -> list[dict]:
        """
        Calculate a flattened Bill of Materials for *quantity* units of *part_id*.
        Only includes parts created by PURCHASE operations (raw materials).
        """
        bom_map: dict[UUID, dict] = {}  # part_id -> {part_id, name, quantity, unit, unit_cost}

        with self.db.session as session:

            def traverse(p_id: UUID, target_qty: float):
                part = session.get(PartNode, p_id)
                if not part or not self.has_access(user_id, part, session):
                    return

                op = session.get(OperationNode, part.created_by_id) if part.created_by_id else None
                if not op:
                    return

                # To get target_qty good units, we need to produce target_qty / yield_rate
                needed_qty = target_qty / op.yield_rate

                if op.op_type == OpType.PURCHASE:
                    if p_id not in bom_map:
                        # Calculate unit cost for purchase from currency inputs
                        statement = select(OperationInputCurrency.quantity).where(OperationInputCurrency.operation_id == op.id)
                        unit_cost = sum(session.exec(statement).all())

                        bom_map[p_id] = {
                            "part_id": str(p_id),
                            "name": part.name,
                            "quantity": 0.0,
                            "unit": part.unit_of_measure,
                            "unit_cost": unit_cost,
                        }
                    bom_map[p_id]["quantity"] += needed_qty
                else:
                    # STANDARD op
                    # Get input parts
                    statement = select(OperationInputParts.part_id, OperationInputParts.quantity).where(OperationInputParts.operation_id == op.id)
                    for inp_p_id, inp_qty in session.exec(statement):
                        traverse(inp_p_id, needed_qty * inp_qty)

        traverse(part_id, quantity)

        # Finalize total costs
        results = []
        for item in bom_map.values():
            item["total_cost"] = item["quantity"] * item["unit_cost"]
            results.append(item)

        return results

    def update_operation_inputs(
        self,
        op_id: UUID,
        input_parts: list[QuantityInput] | None = None,
        input_labor: list[QuantityInput] | None = None,
        input_tools: list[QuantityInput] | None = None,
        input_currencies: list[QuantityInput] | None = None,
    ) -> None:
        """Atomically replace all inputs for an operation."""
        with self.db.session as session:
            try:
                if input_parts is not None:
                    session.exec(delete(OperationInputParts).where(col(OperationInputParts.operation_id) == op_id))
                    for p_in in input_parts:
                        session.add(OperationInputParts(operation_id=op_id, part_id=p_in.resource_id, quantity=p_in.quantity, unit=p_in.unit))

                if input_labor is not None:
                    session.exec(delete(OperationInputLabor).where(col(OperationInputLabor.operation_id) == op_id))
                    for l_in in input_labor:
                        session.add(OperationInputLabor(operation_id=op_id, labor_id=l_in.resource_id, quantity=l_in.quantity, unit=l_in.unit))

                if input_tools is not None:
                    session.exec(delete(OperationInputTools).where(col(OperationInputTools.operation_id) == op_id))
                    for t_in in input_tools:
                        session.add(OperationInputTools(operation_id=op_id, tool_id=t_in.resource_id, quantity=t_in.quantity, unit=t_in.unit))

                if input_currencies is not None:
                    session.exec(delete(OperationInputCurrency).where(col(OperationInputCurrency.operation_id) == op_id))
                    for c_in in input_currencies:
                        session.add(OperationInputCurrency(operation_id=op_id, currency_id=c_in.resource_id, quantity=c_in.quantity, unit=c_in.unit))

                session.commit()
            except Exception:
                session.rollback()
                raise

    # ===============================================================
    # Node Sharing
    # ===============================================================

    def share_node(self, node_id: UUID, user_id: UUID) -> None:
        with self.db.session as session:
            existing = session.exec(select(NodeShare).where(NodeShare.node_id == node_id, NodeShare.user_id == user_id)).first()
            if not existing:
                session.add(NodeShare(node_id=node_id, user_id=user_id))
                session.commit()

    def unshare_node(self, node_id: UUID, user_id: UUID) -> None:
        with self.db.session as session:
            existing = session.exec(select(NodeShare).where(NodeShare.node_id == node_id, NodeShare.user_id == user_id)).first()
            if existing:
                session.delete(existing)
                session.commit()

    def get_node_shares(self, node_id: UUID) -> list[UUID]:
        with self.db.session as session:
            shares = session.exec(select(NodeShare.user_id).where(NodeShare.node_id == node_id)).all()
            return list(shares)

    # ===============================================================
    # Validation
    # ===============================================================

    def validate_tree(self, root_id: UUID, user_id: UUID | None = None) -> ValidationResult:
        """Validate tree from root part."""
        errs: list[ValidationError] = []
        with self.db.session as session:
            root = session.get(PartNode, root_id)
            if root is None or not self.has_access(user_id, root, session):
                return ValidationResult(False, [ValidationError(root_id, "Root not found or access denied")])

            visited: set[UUID] = set()
            queue: list[tuple[BaseNode, set[UUID]]] = [(root, set())]

            while queue:
                node, path = queue.pop(0)
                if node.id in visited:
                    continue

                if node.id in path:
                    errs.append(ValidationError(node.id, f"Cycle detected at node '{node.name}'"))
                    continue

                visited.add(node.id)
                current_path = path | {node.id}

                if isinstance(node, PartNode):
                    if not node.created_by_id:
                        errs.append(ValidationError(node.id, f"Part '{node.name}' has no creator operation."))
                    else:
                        op = session.get(OperationNode, node.created_by_id)
                        if op:
                            queue.append((op, current_path))
                        else:
                            errs.append(ValidationError(node.id, f"Part '{node.name}' creator operation NOT FOUND."))

                elif isinstance(node, OperationNode):
                    # Fetch inputs for validation
                    part_qs = select(OperationInputParts).where(OperationInputParts.operation_id == node.id)
                    labor_qs = select(OperationInputLabor).where(OperationInputLabor.operation_id == node.id)
                    tool_qs = select(OperationInputTools).where(OperationInputTools.operation_id == node.id)
                    curr_qs = select(OperationInputCurrency).where(OperationInputCurrency.operation_id == node.id)

                    parts = list(session.exec(part_qs).all())
                    labors = list(session.exec(labor_qs).all())
                    tools = list(session.exec(tool_qs).all())
                    currs = list(session.exec(curr_qs).all())

                    if node.op_type == OpType.PURCHASE:
                        if parts or labors or tools:
                            errs.append(ValidationError(node.id, f"Purchase Op '{node.name}' has non-currency inputs"))
                        if not currs:
                            errs.append(ValidationError(node.id, f"Purchase Op '{node.name}' has no currency inputs"))
                        for cq in currs:
                            if cq.quantity <= 0:
                                errs.append(ValidationError(node.id, f"Purchase Op '{node.name}' has non-positive cost"))
                            curr_node = session.get(CurrencyNode, cq.currency_id)
                            if curr_node:
                                queue.append((curr_node, current_path))
                    else:  # STANDARD
                        if currs:
                            errs.append(ValidationError(node.id, f"Standard Op '{node.name}' has currency inputs"))
                        if not parts:
                            errs.append(ValidationError(node.id, f"Standard Op '{node.name}' has no input parts"))
                        if not (labors or tools):
                            errs.append(ValidationError(node.id, f"Standard Op '{node.name}' requires Labor or Tool"))
                        if not (0 < node.yield_rate <= 1.0):
                            errs.append(ValidationError(node.id, f"Standard Op '{node.name}' has invalid yield_rate"))

                        for pq in parts:
                            if pq.quantity <= 0:
                                errs.append(ValidationError(node.id, f"Standard Op '{node.name}': non-positive quantity"))
                            p_node = session.get(PartNode, pq.part_id)
                            if p_node:
                                if not self.has_access(user_id, p_node, session):
                                    errs.append(ValidationError(node.id, f"Standard Op '{node.name}': access denied to input part '{p_node.name}'"))
                                else:
                                    queue.append((p_node, current_path))
                        for lq in labors:
                            if lq.quantity <= 0:
                                errs.append(ValidationError(node.id, f"Standard Op '{node.name}': non-positive labor qty"))
                        for tq in tools:
                            if tq.quantity <= 0:
                                errs.append(ValidationError(node.id, f"Standard Op '{node.name}': non-positive tool qty"))

            return ValidationResult(valid=len(errs) == 0, errors=errs)
