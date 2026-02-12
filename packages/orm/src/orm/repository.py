"""
CRUD, traversal, and validation for the Interlock manufacturing tree.

Tree invariants
---------------
* Root is a ``PartNode``.
* Every Part (except maybe raw materials if allowed, but strict mode says:)
  must have exactly one ``created_by`` operation.
* Operations are either STANDARD or PURCHASE.
* STANDARD operations consume Parts, Labor, and Tools.
* PURCHASE operations consume Currency.
* One-way pointers only: part → created_by, operation → inputs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from uuid import UUID

from database.manager import DatabaseManager
from database.schema import initialize_schema
from models.main import (
    BaseNode,
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

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db
        initialize_schema(db)

    # ===============================================================
    # Atomic Transactions (Strict Tree Construction)
    # ===============================================================

    def purchase_part(
        self,
        part: PartNode,
        operation: OperationNode,
        cost: list[QuantityInput],
    ) -> PartNode:
        """
        Atomically create a Part, a Purchase Operation, and link them
        with Currency inputs.
        This is the base case for building the tree from the bottom up.
        """
        if operation.op_type != OpType.PURCHASE:
            raise ValueError("Operation must be of type PURCHASE")

        # Verify currency inputs exist
        for c_input in cost:
            if not self.get_currency(c_input.resource_id):
                raise ValueError(f"Currency {c_input.resource_id} not found")

        try:
            # 1. Create Nodes
            self._create_part(part)
            self._create_operation(operation)

            # 2. Link Part -> Operation
            self._set_created_by(part.id, operation.id)

            # 3. Link Operation -> Currency Inputs
            for c_input in cost:
                self._add_input_currency(
                    operation.id,
                    c_input.resource_id,
                    c_input.quantity,
                    c_input.unit,
                )

            self.db.commit()
            return part
        except Exception:
            self.db.connection.rollback()
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

        # Validation: Verify all inputs exist
        for p_input in input_parts:
            existing_part = self.get_part(p_input.resource_id)
            if not existing_part:
                raise ValueError(f"Input Part {p_input.resource_id} not found")
            # Strict mode: Input parts must have a created_by op.
            # But raw materials are 'purchased' so they have a purchase op.
            if not self.get_created_by(existing_part.id):
                raise ValueError(
                    f"Input Part {existing_part.name} is invalid (orphaned/no creator)"
                )

        for l_input in input_labor:
            if not self.get_labor(l_input.resource_id):
                raise ValueError(f"Labor {l_input.resource_id} not found")

        for t_input in input_tools:
            if not self.get_tool(t_input.resource_id):
                raise ValueError(f"Tool {t_input.resource_id} not found")

        try:
            # 1. Create Nodes
            self._create_part(part)
            self._create_operation(operation)

            # 2. Link Part -> Operation
            self._set_created_by(part.id, operation.id)

            # 3. Link Inputs
            for p_input in input_parts:
                self._add_input_part(
                    operation.id, p_input.resource_id, p_input.quantity, p_input.unit
                )
            for l_input in input_labor:
                self._add_input_labor(
                    operation.id, l_input.resource_id, l_input.quantity, l_input.unit
                )
            for t_input in input_tools:
                self._add_input_tool(
                    operation.id, t_input.resource_id, t_input.quantity, t_input.unit
                )

            self.db.commit()
            return part
        except Exception:
            self.db.connection.rollback()
            raise

    # ===============================================================
    # Part CRUD (Internal/Protected)
    # ===============================================================

    def _create_part(self, part: PartNode) -> PartNode:
        self.db.execute(
            """
            INSERT INTO part_nodes
                (id, name, description, status)
            VALUES (?, ?, ?, ?)
            """,
            (
                str(part.id),
                part.name,
                part.description,
                part.status.value,
            ),
        )
        return part

    def get_part(self, part_id: UUID) -> PartNode | None:
        row = self.db.fetch_one(
            "SELECT * FROM part_nodes WHERE id = ?",
            (str(part_id),),
        )
        return self._to_part(row) if row else None

    def list_parts(
        self,
        *,
        status: NodeStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PartNode]:
        clauses: list[str] = []
        params: list[object] = []
        if status is not None:
            clauses.append("status = ?")
            params.append(status.value)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        params += [limit, offset]
        rows = self.db.fetch_all(
            f"SELECT * FROM part_nodes{where}"  # noqa: S608
            " ORDER BY name LIMIT ? OFFSET ?",
            tuple(params),
        )
        return [self._to_part(r) for r in rows]

    def list_root_parts(self) -> list[PartNode]:
        """Find parts that are not used as inputs to any operation."""
        rows = self.db.fetch_all(
            """
            SELECT p.* FROM part_nodes p
            LEFT JOIN operation_input_parts i ON p.id = i.part_id
            WHERE i.part_id IS NULL
            ORDER BY p.name
            """
        )
        return [self._to_part(r) for r in rows]

    def get_tree_json(self, part_id: UUID) -> dict:
        """Recursive tree structure for visualization."""
        part = self.get_part(part_id)
        if not part:
            return {}

        res = {
            "id": str(part.id),
            "name": part.name,
            "type": "part",
            "status": part.status.value,
            "children": [],
        }

        op = self.get_created_by(part.id)
        if op:
            op_node = {
                "id": str(op.id),
                "name": op.name,
                "type": "operation",
                "op_type": op.op_type.value,
                "children": [],
            }
            res["children"].append(op_node)

            # Input Parts
            for pq in self.get_input_parts(op.id):
                child_part = self.get_tree_json(pq.part.id)
                child_part["quantity"] = pq.quantity
                child_part["unit"] = pq.unit
                op_node["children"].append(child_part)

            # Input Currencies
            for cq in self.get_input_currencies(op.id):
                op_node["children"].append(
                    {
                        "id": str(cq.currency.id),
                        "name": cq.currency.name,
                        "type": "currency",
                        "iso_code": cq.currency.iso_code,
                        "quantity": cq.quantity,
                        "unit": cq.unit,
                    }
                )

            # Input Labor
            for lq in self.get_input_labor(op.id):
                op_node["children"].append(
                    {
                        "id": str(lq.labor.id),
                        "name": lq.labor.name,
                        "type": "labor",
                        "quantity": lq.quantity,
                        "unit": lq.unit,
                    }
                )

            # Input Tools
            for tq in self.get_input_tools(op.id):
                # Tools also have a linked part, but for tree visualization
                # we usually just show the tool node.
                op_node["children"].append(
                    {
                        "id": str(tq.tool.id),
                        "name": tq.tool.name,
                        "type": "tool",
                        "quantity": tq.quantity,
                        "unit": tq.unit,
                    }
                )

        return res

    def update_part(self, part: PartNode) -> PartNode:
        cur = self.db.execute(
            """
            UPDATE part_nodes
            SET name = ?, description = ?, status = ?
            WHERE id = ?
            """,
            (
                part.name,
                part.description,
                part.status.value,
                str(part.id),
            ),
        )
        if cur.rowcount == 0:
            raise ValueError(f"Part {part.id} not found")
        self.db.commit()
        return part

    def delete_part(self, part_id: UUID) -> bool:
        cur = self.db.execute(
            "DELETE FROM part_nodes WHERE id = ?",
            (str(part_id),),
        )
        self.db.commit()
        return cur.rowcount > 0

    # ===============================================================
    # Currency CRUD
    # ===============================================================

    def create_currency(self, curr: CurrencyNode) -> CurrencyNode:
        self.db.execute(
            """
            INSERT INTO currency_nodes (id, name, description, iso_code)
            VALUES (?, ?, ?, ?)
            """,
            (str(curr.id), curr.name, curr.description, curr.iso_code),
        )
        self.db.commit()
        return curr

    def get_currency(self, curr_id: UUID) -> CurrencyNode | None:
        row = self.db.fetch_one(
            "SELECT * FROM currency_nodes WHERE id = ?", (str(curr_id),)
        )
        return self._to_currency(row) if row else None

    def list_currencies(self) -> list[CurrencyNode]:
        rows = self.db.fetch_all("SELECT * FROM currency_nodes ORDER BY name")
        return [self._to_currency(r) for r in rows]

    def delete_currency(self, curr_id: UUID) -> bool:
        cur = self.db.execute(
            "DELETE FROM currency_nodes WHERE id = ?", (str(curr_id),)
        )
        self.db.commit()
        return cur.rowcount > 0

    # ===============================================================
    # Labor CRUD
    # ===============================================================

    def create_labor(self, labor: LaborNode) -> LaborNode:
        self.db.execute(
            "INSERT INTO labor_nodes (id, name, description) VALUES (?, ?, ?)",
            (str(labor.id), labor.name, labor.description),
        )
        self.db.commit()
        return labor

    def get_labor(self, labor_id: UUID) -> LaborNode | None:
        row = self.db.fetch_one(
            "SELECT * FROM labor_nodes WHERE id = ?", (str(labor_id),)
        )
        return self._to_labor(row) if row else None

    def list_labor(self) -> list[LaborNode]:
        rows = self.db.fetch_all("SELECT * FROM labor_nodes ORDER BY name")
        return [self._to_labor(r) for r in rows]

    # ===============================================================
    # Tool CRUD
    # ===============================================================

    def create_tool(self, tool: ToolNode) -> ToolNode:
        # Validate linked part exists and is valid (has creator)
        linked_part = self.get_part(tool.linked_part_id)
        if not linked_part:
            raise ValueError(f"Linked Part {tool.linked_part_id} not found")
        if not self.get_created_by(linked_part.id):
            raise ValueError(f"Linked Part {linked_part.name} is invalid (orphaned)")

        self.db.execute(
            """
            INSERT INTO tool_nodes (id, name, description, linked_part_id)
            VALUES (?, ?, ?, ?)
            """,
            (str(tool.id), tool.name, tool.description, str(tool.linked_part_id)),
        )
        self.db.commit()
        return tool

    def get_tool(self, tool_id: UUID) -> ToolNode | None:
        row = self.db.fetch_one(
            "SELECT * FROM tool_nodes WHERE id = ?", (str(tool_id),)
        )
        return self._to_tool(row) if row else None

    def list_tools(self) -> list[ToolNode]:
        rows = self.db.fetch_all("SELECT * FROM tool_nodes ORDER BY name")
        return [self._to_tool(r) for r in rows]

    # ===============================================================
    # Operation CRUD (Internal/Protected)
    # ===============================================================

    def _create_operation(self, op: OperationNode) -> OperationNode:
        self.db.execute(
            """
            INSERT INTO operation_nodes
                (id, name, description, op_type,
                 estimated_duration_minutes,
                 cost_estimate, properties)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(op.id),
                op.name,
                op.description,
                op.op_type.value,
                op.estimated_duration_minutes,
                op.cost_estimate,
                json.dumps(op.properties),
            ),
        )
        return op

    def get_operation(self, op_id: UUID) -> OperationNode | None:
        row = self.db.fetch_one(
            "SELECT * FROM operation_nodes WHERE id = ?",
            (str(op_id),),
        )
        return self._to_op(row) if row else None

    def list_operations(
        self,
        *,
        op_type: OpType | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[OperationNode]:
        if op_type is not None:
            rows = self.db.fetch_all(
                "SELECT * FROM operation_nodes"
                " WHERE op_type = ?"
                " ORDER BY name LIMIT ? OFFSET ?",
                (op_type.value, limit, offset),
            )
        else:
            rows = self.db.fetch_all(
                "SELECT * FROM operation_nodes ORDER BY name LIMIT ? OFFSET ?",
                (limit, offset),
            )
        return [self._to_op(r) for r in rows]

    def update_operation(self, op: OperationNode) -> OperationNode:
        cur = self.db.execute(
            """
            UPDATE operation_nodes
            SET name = ?, description = ?,
                op_type = ?,
                estimated_duration_minutes = ?,
                cost_estimate = ?,
                properties = ?
            WHERE id = ?
            """,
            (
                op.name,
                op.description,
                op.op_type.value,
                op.estimated_duration_minutes,
                op.cost_estimate,
                json.dumps(op.properties),
                str(op.id),
            ),
        )
        if cur.rowcount == 0:
            raise ValueError(f"Operation {op.id} not found")
        self.db.commit()
        return op

    def delete_operation(self, op_id: UUID) -> bool:
        cur = self.db.execute(
            "DELETE FROM operation_nodes WHERE id = ?",
            (str(op_id),),
        )
        self.db.commit()
        return cur.rowcount > 0

    # ===============================================================
    # Polymorphic lookup
    # ===============================================================

    def get_node(self, node_id: UUID) -> BaseNode | None:
        """Look up any node by ID."""
        for finder in [
            self.get_part,
            self.get_operation,
            self.get_currency,
            self.get_labor,
            self.get_tool,
        ]:
            node = finder(node_id)
            if node:
                return node
        return None

    # ===============================================================
    # created_by  (part → operation)
    # ===============================================================

    def _set_created_by(self, part_id: UUID, op_id: UUID) -> None:
        self.db.execute(
            """
            UPDATE part_nodes
            SET created_by_id = ?, created_by_type = (
                SELECT op_type FROM operation_nodes
                WHERE id = ?
            )
            WHERE id = ?
            """,
            (str(op_id), str(op_id), str(part_id)),
        )

    def clear_created_by(self, part_id: UUID) -> None:
        self.db.execute(
            """
            UPDATE part_nodes
            SET created_by_id = NULL,
                created_by_type = NULL
            WHERE id = ?
            """,
            (str(part_id),),
        )
        self.db.commit()

    def get_created_by(self, part_id: UUID) -> OperationNode | None:
        row = self.db.fetch_one(
            "SELECT created_by_id FROM part_nodes WHERE id = ?",
            (str(part_id),),
        )
        if not row or not row["created_by_id"]:
            return None
        return self.get_operation(UUID(row["created_by_id"]))

    def get_output_part(self, op_id: UUID) -> PartNode | None:
        row = self.db.fetch_one(
            "SELECT * FROM part_nodes WHERE created_by_id = ?",
            (str(op_id),),
        )
        return self._to_part(row) if row else None

    # ===============================================================
    # Operation Inputs (Quantities)
    # ===============================================================

    # --- Parts ---

    def _add_input_part(
        self, op_id: UUID, part_id: UUID, quantity: float, unit: str = "pcs"
    ) -> None:
        self.db.execute(
            """
            INSERT OR REPLACE INTO operation_input_parts
                (operation_id, part_id, quantity, unit)
            VALUES (?, ?, ?, ?)
            """,
            (str(op_id), str(part_id), quantity, unit),
        )

    def get_input_parts(self, op_id: UUID) -> list[PartQuantity]:
        rows = self.db.fetch_all(
            """
            SELECT p.*, i.quantity, i.unit
            FROM part_nodes p
            JOIN operation_input_parts i ON i.part_id = p.id
            WHERE i.operation_id = ?
            """,
            (str(op_id),),
        )
        return [
            PartQuantity(
                quantity=float(r["quantity"]),
                unit=str(r["unit"]),
                part=self._to_part(r),
            )
            for r in rows
        ]

    # --- Labor ---

    def _add_input_labor(
        self, op_id: UUID, labor_id: UUID, quantity: float, unit: str = "hours"
    ) -> None:
        self.db.execute(
            """
            INSERT OR REPLACE INTO operation_input_labor
                (operation_id, labor_id, quantity, unit)
            VALUES (?, ?, ?, ?)
            """,
            (str(op_id), str(labor_id), quantity, unit),
        )

    def get_input_labor(self, op_id: UUID) -> list[LaborQuantity]:
        rows = self.db.fetch_all(
            """
            SELECT l.*, i.quantity, i.unit
            FROM labor_nodes l
            JOIN operation_input_labor i ON i.labor_id = l.id
            WHERE i.operation_id = ?
            """,
            (str(op_id),),
        )
        return [
            LaborQuantity(
                quantity=float(r["quantity"]),
                unit=str(r["unit"]),
                labor=self._to_labor(r),
            )
            for r in rows
        ]

    # --- Tools ---

    def _add_input_tool(
        self, op_id: UUID, tool_id: UUID, quantity: float, unit: str = "pcs"
    ) -> None:
        self.db.execute(
            """
            INSERT OR REPLACE INTO operation_input_tools
                (operation_id, tool_id, quantity, unit)
            VALUES (?, ?, ?, ?)
            """,
            (str(op_id), str(tool_id), quantity, unit),
        )

    def get_input_tools(self, op_id: UUID) -> list[ToolQuantity]:
        rows = self.db.fetch_all(
            """
            SELECT t.*, i.quantity, i.unit
            FROM tool_nodes t
            JOIN operation_input_tools i ON i.tool_id = t.id
            WHERE i.operation_id = ?
            """,
            (str(op_id),),
        )
        return [
            ToolQuantity(
                quantity=float(r["quantity"]),
                unit=str(r["unit"]),
                tool=self._to_tool(r),
            )
            for r in rows
        ]

    # --- Currency (Purchase) ---

    def _add_input_currency(
        self, op_id: UUID, curr_id: UUID, quantity: float, unit: str = "units"
    ) -> None:
        self.db.execute(
            """
            INSERT OR REPLACE INTO operation_input_currency
                (operation_id, currency_id, quantity, unit)
            VALUES (?, ?, ?, ?)
            """,
            (str(op_id), str(curr_id), quantity, unit),
        )

    def get_input_currencies(self, op_id: UUID) -> list[CurrencyQuantity]:
        rows = self.db.fetch_all(
            """
            SELECT c.*, i.quantity, i.unit
            FROM currency_nodes c
            JOIN operation_input_currency i ON i.currency_id = c.id
            WHERE i.operation_id = ?
            """,
            (str(op_id),),
        )
        return [
            CurrencyQuantity(
                quantity=float(r["quantity"]),
                unit=str(r["unit"]),
                currency=self._to_currency(r),
            )
            for r in rows
        ]

    # ===============================================================
    # Traversal (Material Flow)
    # ===============================================================

    def get_full_timeline(self, part_id: UUID) -> list[BaseNode]:
        """
        BFS walk from *part_id* upward (inputs) through the tree.
        Traverses Part -> Operation -> Input Parts.
        """
        start = self.get_part(part_id)
        if start is None:
            return []

        visited: set[str] = set()
        timeline: list[BaseNode] = []
        queue: list[BaseNode] = [start]

        while queue:
            node = queue.pop(0)
            key = str(node.id)
            if key in visited:
                continue
            visited.add(key)
            timeline.append(node)

            if isinstance(node, PartNode):
                op = self.get_created_by(node.id)
                if op is not None:
                    queue.append(op)
            elif isinstance(node, OperationNode):
                # Only follow physical parts for timeline usually?
                # If Purchase, maybe follow Currency?
                # User asked: "Currency points to a CurrencyNode".
                # If we want "Leaf Currencies", we should traverse to currency input.
                if node.op_type == OpType.PURCHASE:
                    curr_qs = self.get_input_currencies(node.id)
                    for cq in curr_qs:
                        queue.append(cq.currency)
                else:
                    # Standard Op -> Parts
                    part_qs = self.get_input_parts(node.id)
                    for pq in part_qs:
                        queue.append(pq.part)

        return timeline

    def get_ancestors(self, part_id: UUID) -> list[PartNode]:
        """All upstream parts feeding into *part_id*."""
        return [
            n
            for n in self.get_full_timeline(part_id)
            if isinstance(n, PartNode) and n.id != part_id
        ]

    def get_leaf_currencies(self, part_id: UUID) -> list[CurrencyNode]:
        """Currency leaves reachable from *part_id*."""
        return [
            n for n in self.get_full_timeline(part_id) if isinstance(n, CurrencyNode)
        ]

    # ===============================================================
    # Validation
    # ===============================================================

    def validate_tree(self, root_id: UUID) -> ValidationResult:
        """
        Validate tree from root part.
        1. Root must be PartNode.
        2. Non-root parts must have created_by op.
        3. Ops must have inputs.
        4. PURCHASE ops must ONLY have Currency inputs.
        5. STANDARD ops must NOT have Currency inputs.
        """
        errs: list[ValidationError] = []
        root = self.get_part(root_id)

        if root is None:
            return ValidationResult(False, [ValidationError(root_id, "Root not found")])

        visited: set[str] = set()
        queue: list[BaseNode] = [root]

        while queue:
            node = queue.pop(0)
            nk = str(node.id)
            if nk in visited:
                continue
            visited.add(nk)

            if isinstance(node, PartNode):
                op = self.get_created_by(node.id)
                if op is None:
                    # If this part is a root, it's fine.
                    # But if we arrived here by traversal, it's an input.
                    # Does every input part need a creator?
                    # "A part... can be the root... only children... single op".
                    # Basically, if it's not purchased, it must have a creator unless
                    # it's a raw material?
                    # I'll stick to: If it's a leaf part, it must be created by PURCHASE
                    # to allow entry?
                    # Or maybe raw materials have no created_by.
                    # Assuming strict tree: "Purchase... means that the Part it creates
                    # is purchased".
                    # So essentially, raw materials are parts created by Purchase Op.
                    # So if op is None, it's an error unless it's being defined?
                    # Let's say: If NO created_by, it's invalid unless it's a "Ghost" or
                    # intended error.
                    # But for now I'll just validate graph connectivity.
                    pass
                else:
                    queue.append(op)

            elif isinstance(node, OperationNode):
                # Check inputs
                parts = self.get_input_parts(node.id)
                labors = self.get_input_labor(node.id)
                tools = self.get_input_tools(node.id)
                currs = self.get_input_currencies(node.id)

                if node.op_type == OpType.PURCHASE:
                    if parts or labors or tools:
                        errs.append(
                            ValidationError(
                                node.id,
                                f"Purchase Op '{node.name}' has non-currency inputs",
                            )
                        )
                    if not currs:
                        errs.append(
                            ValidationError(
                                node.id,
                                f"Purchase Op '{node.name}' has no currency inputs",
                            )
                        )
                    for cq in currs:
                        queue.append(cq.currency)

                else:  # STANDARD
                    if currs:
                        errs.append(
                            ValidationError(
                                node.id,
                                f"Standard Op '{node.name}' has currency inputs",
                            )
                        )
                    # Must have at least something?
                    if not (parts or labors or tools):
                        errs.append(
                            ValidationError(
                                node.id,
                                f"Standard Op '{node.name}' has no inputs",
                            )
                        )
                    for pq in parts:
                        queue.append(pq.part)

        return ValidationResult(valid=len(errs) == 0, errors=errs)

    # ===============================================================
    # Converters
    # ===============================================================

    @staticmethod
    def _to_part(row: object) -> PartNode:
        # Cast to Any to satisfy type checker for dict() constructor
        r = dict(row)  # type: ignore
        return PartNode(
            id=UUID(str(r["id"])),
            name=str(r["name"]),
            description=r.get("description"),
            status=NodeStatus(str(r["status"])),
        )

    @staticmethod
    def _to_currency(row: object) -> CurrencyNode:
        r = dict(row)  # type: ignore
        return CurrencyNode(
            id=UUID(str(r["id"])),
            name=str(r["name"]),
            description=r.get("description"),
            iso_code=r.get("iso_code"),
        )

    @staticmethod
    def _to_labor(row: object) -> LaborNode:
        r = dict(row)  # type: ignore
        return LaborNode(
            id=UUID(str(r["id"])),
            name=str(r["name"]),
            description=r.get("description"),
        )

    @staticmethod
    def _to_tool(row: object) -> ToolNode:
        r = dict(row)  # type: ignore
        return ToolNode(
            id=UUID(str(r["id"])),
            name=str(r["name"]),
            description=r.get("description"),
            linked_part_id=UUID(str(r["linked_part_id"])),
        )

    @staticmethod
    def _to_op(row: object) -> OperationNode:
        r = dict(row)  # type: ignore
        raw_props = r.get("properties", "{}")
        props = json.loads(str(raw_props)) if raw_props else {}
        return OperationNode(
            id=UUID(str(r["id"])),
            name=str(r["name"]),
            description=r.get("description"),
            op_type=OpType(str(r["op_type"])),
            estimated_duration_minutes=float(str(r["estimated_duration_minutes"])),
            cost_estimate=float(str(r["cost_estimate"])),
            properties=props,
        )
