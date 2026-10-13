"""saved_audit_filters.is_default (team-wide pinned default)

Revision ID: f2b3c4d5e6f7
Revises: e1f2a3b4c5d6
Create Date: 2026-06-15
"""
from alembic import op
import sqlalchemy as sa

revision = "f2b3c4d5e6f7"
down_revision = "e1f2a3b4c5d6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "saved_audit_filters",
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade():
    op.drop_column("saved_audit_filters", "is_default")
