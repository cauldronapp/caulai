"""saved_audit_filters table

Revision ID: e1f2a3b4c5d6
Revises: d88e3be3f8b8
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e1f2a3b4c5d6"
down_revision = "d88e3be3f8b8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "saved_audit_filters",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("owner_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("query", postgresql.JSONB(), nullable=False),
        sa.Column("shared", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_saved_audit_filters_owner_id", "saved_audit_filters", ["owner_id"])


def downgrade():
    op.drop_index("ix_saved_audit_filters_owner_id", table_name="saved_audit_filters")
    op.drop_table("saved_audit_filters")
