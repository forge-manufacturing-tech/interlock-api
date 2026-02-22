"""add_ownership_and_sharing

Revision ID: b4ab591f4965
Revises: 989ad1febd22
Create Date: 2026-02-21 17:28:01.787891

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b4ab591f4965"
down_revision: str | Sequence[str] | None = "989ad1febd22"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. Create node_shares
    if "node_shares" not in existing_tables:
        op.create_table(
            "node_shares",
            sa.Column("node_id", sa.Uuid(), nullable=False),
            sa.Column("user_id", sa.Uuid(), nullable=False),
            sa.PrimaryKeyConstraint("node_id", "user_id"),
        )

    tables = ["currency_nodes", "labor_nodes", "operation_nodes", "part_nodes", "tool_nodes"]
    for table in tables:
        columns = [c["name"] for c in inspector.get_columns(table)]

        if "owner_id" not in columns:
            op.add_column(table, sa.Column("owner_id", sa.Uuid(), nullable=True))
        if "is_public" not in columns:
            op.add_column(table, sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("true")))
        if "project_label" not in columns:
            op.add_column(table, sa.Column("project_label", sa.String(), nullable=True))

        # Indices (Alembic doesn't have create_index_if_not_exists, so we check inspector)
        indices = [i["name"] for i in inspector.get_indexes(table)]
        if f"ix_{table}_is_public" not in indices:
            op.create_index(f"ix_{table}_is_public", table, ["is_public"])
        if f"ix_{table}_owner_id" not in indices:
            op.create_index(f"ix_{table}_owner_id", table, ["owner_id"])
        if f"ix_{table}_project_label" not in indices:
            op.create_index(f"ix_{table}_project_label", table, ["project_label"])


def downgrade() -> None:
    """Downgrade schema."""
    tables = ["currency_nodes", "labor_nodes", "operation_nodes", "part_nodes", "tool_nodes"]
    for table in tables:
        op.drop_index(f"ix_{table}_project_label", table_name=table)
        op.drop_index(f"ix_{table}_owner_id", table_name=table)
        op.drop_index(f"ix_{table}_is_public", table_name=table)
        op.drop_column(table, "project_label")
        op.drop_column(table, "is_public")
        op.drop_column(table, "owner_id")

    op.drop_table("node_shares")
