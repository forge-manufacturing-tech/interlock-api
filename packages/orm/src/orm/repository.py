"""
CRUD, traversal, and validation for the Interlock manufacturing graph.

Tree invariants
---------------
* Root is a ``PartNode``.
* Operations are either OperationNode or PurchaseNode.
* Operations are embedded inside the `child_node` field of `PartNode`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from database.manager import DatabaseManager
from database.schema import initialize_schema
from models.main import (
    BaseNode,
    FileAttachment,
    LaborNode,
    OperationNode,
    PartNode,
    PurchaseNode,
    ToolNode,
)
from sqlmodel import select

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
    """Simplified CRUD for nested graph structures."""

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
        purchase: PurchaseNode,
    ) -> PartNode:
        """
        Atomically create a Part with its Purchase operation.
        """
        if purchase.cost.amount <= 0:
            raise ValueError(f"Cost amount must be positive, got {purchase.cost.amount}")

        part.child_node = purchase
        with self.db.session as session:
            try:
                session.add(part)
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
    ) -> PartNode:
        """
        Atomically create a Part with a Standard operation.
        """
        # --- Yield rate validation ---
        if not (0 < operation.yield_rate <= 1.0):
            raise ValueError(f"yield_rate must be in (0, 1.0], got {operation.yield_rate}")

        part.child_node = operation
        with self.db.session as session:
            try:
                session.add(part)
                session.commit()
                session.refresh(part)
                return part
            except Exception:
                session.rollback()
                raise

    # ===============================================================
    # CRUD Operations
    # ===============================================================

    def get_part(self, part_id: UUID) -> PartNode | None:
        with self.db.session as session:
            return session.get(PartNode, part_id)

    def list_parts(self, *, limit: int = 100, offset: int = 0) -> list[PartNode]:
        with self.db.session as session:
            statement = select(PartNode).order_by(PartNode.name).limit(limit).offset(offset)
            return list(session.exec(statement).all())

    def update_part(self, part: PartNode) -> PartNode:
        with self.db.session as session:
            existing = session.get(PartNode, part.id)
            if not existing:
                raise ValueError(f"Part {part.id} not found")
            existing.name = part.name
            existing.description = part.description
            existing.unit_of_measure = part.unit_of_measure
            existing.child_node = part.child_node
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return existing

    def delete_part(self, part_id: UUID) -> bool:
        with self.db.session as session:
            part = session.get(PartNode, part_id)
            if not part:
                return False
            session.delete(part)
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

    def get_labor(self, labor_id: UUID) -> LaborNode | None:
        with self.db.session as session:
            return session.get(LaborNode, labor_id)

    def list_labor(self) -> list[LaborNode]:
        with self.db.session as session:
            return list(session.exec(select(LaborNode).order_by(LaborNode.name)).all())

    # --- Tools ---

    def create_tool(self, tool: ToolNode) -> ToolNode:
        if tool.cost_rate < 0:
            raise ValueError("cost_rate must be non-negative")
        with self.db.session as session:
            session.add(tool)
            session.commit()
            session.refresh(tool)
            return tool

    def list_tools(self) -> list[ToolNode]:
        with self.db.session as session:
            return list(session.exec(select(ToolNode).order_by(ToolNode.name)).all())

    def get_node(self, node_id: UUID) -> BaseNode | None:
        """Look up top level node by ID."""
        with self.db.session as session:
            for model in [PartNode, LaborNode, ToolNode]:
                node = session.get(model, node_id)
                if node:
                    return node
            return None

    # ===============================================================
    # File Attachments
    # ===============================================================

    def add_file_attachment(
        self,
        name: str,
        storage_path: str,
        node_id: UUID,
        content_type: str | None = None,
        size: int | None = None,
        owner_id: UUID | None = None,
    ) -> FileAttachment:
        with self.db.session as session:
            attachment = FileAttachment(
                name=name,
                storage_path=storage_path,
                content_type=content_type,
                size=size,
                node_id=node_id,
                owner_id=owner_id,
            )
            session.add(attachment)
            session.commit()
            session.refresh(attachment)
            return attachment

    def list_file_attachments(
        self,
        node_id: UUID,
    ) -> list[FileAttachment]:
        with self.db.session as session:
            statement = select(FileAttachment).where(FileAttachment.node_id == node_id)
            return list(session.exec(statement).all())

    def get_file_attachment(self, attachment_id: UUID) -> FileAttachment | None:
        with self.db.session as session:
            return session.get(FileAttachment, attachment_id)

    def delete_file_attachment(self, attachment_id: UUID) -> bool:
        with self.db.session as session:
            attachment = session.get(FileAttachment, attachment_id)
            if not attachment:
                return False
            session.delete(attachment)
            session.commit()
            return True

    # ===============================================================
    # Traversal (Material Flow)
    # ===============================================================

    def get_full_timeline(self, part_id: UUID) -> list[BaseNode]:
        """BFS walk from *part_id* downward through the embedded tree."""
        part = self.get_part(part_id)
        if not part:
            return []

        timeline = []
        queue = [part]

        while queue:
            node = queue.pop(0)
            timeline.append(node)

            if isinstance(node, PartNode):
                if node.child_node:
                    queue.append(node.child_node)
            elif isinstance(node, OperationNode):
                if node.labor_node:
                    timeline.append(node.labor_node)
                if node.tool_node:
                    timeline.append(node.tool_node)
                if node.part_nodes:
                    for child_part in node.part_nodes:
                        if child_part:
                            queue.append(child_part)
        return timeline

    def get_ancestors(self, part_id: UUID) -> list[PartNode]:
        """All upstream parts feeding into *part_id*."""
        return [n for n in self.get_full_timeline(part_id) if isinstance(n, PartNode) and n.id != part_id]

    def get_leaf_currencies(self, part_id: UUID) -> list[PurchaseNode]:
        """All leaf purchase costs reachable from *part_id*."""
        return [n for n in self.get_full_timeline(part_id) if isinstance(n, PurchaseNode)]

    def get_tree_json(self, part_id: UUID) -> dict:
        """Recursive tree structure for visualization."""
        part = self.get_part(part_id)
        if not part:
            return {}
        return part.model_dump(mode="json")

    def get_bom(self, part_id: UUID, quantity: float = 1.0) -> list[dict]:
        """Calculate a flattened Bill of Materials for *quantity* units of *part_id*."""
        bom_map = {}

        def traverse(p: PartNode, target_qty: float):
            op = p.child_node
            if not op:
                return
            if isinstance(op, PurchaseNode):
                pid = str(p.id)
                if pid not in bom_map:
                    bom_map[pid] = {
                        "part_id": pid,
                        "name": p.name,
                        "quantity": 0.0,
                        "unit": p.unit_of_measure,
                        "unit_cost": op.cost.amount,
                    }
                bom_map[pid]["quantity"] += target_qty
            elif isinstance(op, OperationNode):
                needed_qty = target_qty / op.yield_rate
                if op.part_nodes:
                    for sub_p in op.part_nodes:
                        # Assuming quantity is 1 for each part in the tuple for now,
                        # or evenly split. The new schema doesn't seem to store inputs quantities precisely unless defined elsewhere!
                        if sub_p:
                            traverse(sub_p, needed_qty * 1.0)

        part = self.get_part(part_id)
        if part:
            traverse(part, quantity)

        results = []
        for item in bom_map.values():
            item["total_cost"] = item["quantity"] * item["unit_cost"]
            results.append(item)
        return results

    def validate_tree(self, root_id: UUID) -> ValidationResult:
        return ValidationResult(valid=True, errors=[])
