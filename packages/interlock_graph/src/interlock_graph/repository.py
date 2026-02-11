"""
CRUD, traversal, and validation for the Interlock manufacturing tree.

Tree invariants
---------------
* Root is a non-currency ``PartNode``.
* Leaves are currency ``PartNode``\\s (``is_currency=True``).
* Every non-currency part has exactly one ``created_by`` operation.
* Every operation has ≥ 1 input part.
* ``PURCHASE`` operation inputs must ALL be currency nodes.
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
    NodeStatus,
    OperationNode,
    OpType,
    PartNode,
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
    # Part CRUD
    # ===============================================================

    def create_part(self, part: PartNode) -> PartNode:
        self.db.execute(
            """
            INSERT INTO part_nodes
                (id, name, description, status, is_currency)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(part.id),
                part.name,
                part.description,
                part.status.value,
                int(part.is_currency),
            ),
        )
        self.db.commit()
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
        is_currency: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PartNode]:
        clauses: list[str] = []
        params: list[object] = []
        if status is not None:
            clauses.append("status = ?")
            params.append(status.value)
        if is_currency is not None:
            clauses.append("is_currency = ?")
            params.append(int(is_currency))
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        params += [limit, offset]
        rows = self.db.fetch_all(
            f"SELECT * FROM part_nodes{where}"  # noqa: S608
            " ORDER BY name LIMIT ? OFFSET ?",
            tuple(params),
        )
        return [self._to_part(r) for r in rows]

    def update_part(self, part: PartNode) -> PartNode:
        cur = self.db.execute(
            """
            UPDATE part_nodes
            SET name = ?, description = ?,
                status = ?, is_currency = ?
            WHERE id = ?
            """,
            (
                part.name,
                part.description,
                part.status.value,
                int(part.is_currency),
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
    # Operation CRUD
    # ===============================================================

    def create_operation(self, op: OperationNode) -> OperationNode:
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
        self.db.commit()
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
        """Look up any node (part or operation) by ID."""
        part = self.get_part(node_id)
        if part is not None:
            return part
        return self.get_operation(node_id)

    # ===============================================================
    # created_by  (part → operation)
    # ===============================================================

    def set_created_by(self, part_id: UUID, op_id: UUID) -> None:
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
        self.db.commit()

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
        """The part produced by an operation."""
        row = self.db.fetch_one(
            "SELECT * FROM part_nodes WHERE created_by_id = ?",
            (str(op_id),),
        )
        return self._to_part(row) if row else None

    # ===============================================================
    # inputs  (operation → consumed parts)
    # ===============================================================

    def add_input(self, op_id: UUID, part_id: UUID) -> None:
        self.db.execute(
            """
            INSERT OR IGNORE INTO operation_inputs
                (operation_id, part_id)
            VALUES (?, ?)
            """,
            (str(op_id), str(part_id)),
        )
        self.db.commit()

    def remove_input(self, op_id: UUID, part_id: UUID) -> bool:
        cur = self.db.execute(
            """
            DELETE FROM operation_inputs
            WHERE operation_id = ? AND part_id = ?
            """,
            (str(op_id), str(part_id)),
        )
        self.db.commit()
        return cur.rowcount > 0

    def get_inputs(self, op_id: UUID) -> list[PartNode]:
        rows = self.db.fetch_all(
            """
            SELECT p.* FROM part_nodes p
            JOIN operation_inputs oi ON oi.part_id = p.id
            WHERE oi.operation_id = ?
            """,
            (str(op_id),),
        )
        return [self._to_part(r) for r in rows]

    def get_consumers(self, part_id: UUID) -> list[OperationNode]:
        """Operations that consume this part."""
        rows = self.db.fetch_all(
            "SELECT operation_id FROM operation_inputs WHERE part_id = ?",
            (str(part_id),),
        )
        ops: list[OperationNode] = []
        for r in rows:
            op = self.get_operation(UUID(r["operation_id"]))
            if op:
                ops.append(op)
        return ops

    # ===============================================================
    # equipment  (operation → non-consumed tool/equipment parts)
    # ===============================================================

    def add_equipment(self, op_id: UUID, part_id: UUID) -> None:
        self.db.execute(
            """
            INSERT OR IGNORE INTO operation_equipment
                (operation_id, part_id)
            VALUES (?, ?)
            """,
            (str(op_id), str(part_id)),
        )
        self.db.commit()

    def remove_equipment(self, op_id: UUID, part_id: UUID) -> bool:
        cur = self.db.execute(
            """
            DELETE FROM operation_equipment
            WHERE operation_id = ? AND part_id = ?
            """,
            (str(op_id), str(part_id)),
        )
        self.db.commit()
        return cur.rowcount > 0

    def get_equipment(self, op_id: UUID) -> list[PartNode]:
        """Non-consumed tools / equipment for an operation."""
        rows = self.db.fetch_all(
            """
            SELECT p.* FROM part_nodes p
            JOIN operation_equipment oe
                ON oe.part_id = p.id
            WHERE oe.operation_id = ?
            """,
            (str(op_id),),
        )
        return [self._to_part(r) for r in rows]

    # ===============================================================
    # Traversal
    # ===============================================================

    def get_full_timeline(self, part_id: UUID) -> list[BaseNode]:
        """
        BFS walk from *part_id* upward through the tree
        to the currency leaves.

        Returns ``[root_part, op, input_part, op, …, currency]``.
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
                queue.extend(self.get_inputs(node.id))

        return timeline

    def get_ancestors(self, part_id: UUID) -> list[PartNode]:
        """All upstream parts feeding into *part_id*."""
        return [
            n
            for n in self.get_full_timeline(part_id)
            if isinstance(n, PartNode) and n.id != part_id
        ]

    def get_leaf_currencies(self, part_id: UUID) -> list[PartNode]:
        """Currency leaves reachable from *part_id*."""
        return [
            n
            for n in self.get_full_timeline(part_id)
            if isinstance(n, PartNode) and n.is_currency
        ]

    # ===============================================================
    # Validation
    # ===============================================================

    def validate_tree(self, root_id: UUID) -> ValidationResult:
        """
        Validate the tree rooted at *root_id*.

        Rules
        -----
        1. Root must be a non-currency PartNode.
        2. Leaf parts (no created_by) must be currency.
        3. Non-currency parts must have created_by.
        4. Every operation must have ≥ 1 input.
        5. PURCHASE inputs must all be currency.
        """
        errs: list[ValidationError] = []
        root = self.get_part(root_id)

        if root is None:
            return ValidationResult(
                valid=False,
                errors=[ValidationError(root_id, "Root not found")],
            )
        if root.is_currency:
            errs.append(
                ValidationError(
                    root_id,
                    "Root must not be currency",
                )
            )

        visited_p: set[str] = set()
        visited_o: set[str] = set()
        queue: list[PartNode] = [root]

        while queue:
            part = queue.pop(0)
            pk = str(part.id)
            if pk in visited_p:
                continue
            visited_p.add(pk)

            op = self.get_created_by(part.id)

            if op is None:
                # Rule 2
                if not part.is_currency:
                    errs.append(
                        ValidationError(
                            part.id,
                            f"Leaf '{part.name}' is not currency",
                        )
                    )
                continue

            # Rule 3
            if part.is_currency:
                errs.append(
                    ValidationError(
                        part.id,
                        "Currency node should not have created_by",
                    )
                )

            ok = str(op.id)
            if ok in visited_o:
                continue
            visited_o.add(ok)

            inputs = self.get_inputs(op.id)

            # Rule 4
            if not inputs:
                errs.append(
                    ValidationError(
                        op.id,
                        f"Op '{op.name}' has no inputs",
                    )
                )

            # Rule 5
            if op.op_type == OpType.PURCHASE:
                for inp in inputs:
                    if not inp.is_currency:
                        errs.append(
                            ValidationError(
                                op.id,
                                f"Purchase '{op.name}'"
                                " has non-currency input"
                                f" '{inp.name}'",
                            )
                        )

            queue.extend(inputs)

        return ValidationResult(valid=len(errs) == 0, errors=errs)

    # ===============================================================
    # Row → model converters
    # ===============================================================

    @staticmethod
    def _to_part(row: object) -> PartNode:
        r: dict[str, object] = dict(row)  # type: ignore[arg-type]
        return PartNode(
            id=UUID(str(r["id"])),
            name=str(r["name"]),
            description=(str(r["description"]) if r.get("description") else None),
            status=NodeStatus(str(r["status"])),
            is_currency=bool(r.get("is_currency")),
        )

    @staticmethod
    def _to_op(row: object) -> OperationNode:
        r: dict[str, object] = dict(row)  # type: ignore[arg-type]
        raw_props = r.get("properties", "{}")
        props: dict[str, object] = json.loads(str(raw_props)) if raw_props else {}
        return OperationNode(
            id=UUID(str(r["id"])),
            name=str(r["name"]),
            description=(str(r["description"]) if r.get("description") else None),
            op_type=OpType(str(r["op_type"])),
            estimated_duration_minutes=float(str(r["estimated_duration_minutes"])),
            cost_estimate=float(str(r["cost_estimate"])),
            properties=props,
        )
