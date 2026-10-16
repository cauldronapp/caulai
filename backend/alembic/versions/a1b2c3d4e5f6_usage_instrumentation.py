"""usage instrumentation (dev-only Stage-1 value measurement)

Revision ID: a1b2c3d4e5f6
Revises: f2b3c4d5e6f7
Create Date: 2026-06-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "a1b2c3d4e5f6"
down_revision = "f2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "usage_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("event_type", sa.String(length=48), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("env", sa.String(length=16), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("workflow_type", sa.String(length=48), nullable=False),
        sa.Column("workflow_run_id", sa.String(length=36), nullable=False),
        sa.Column("actor_type", sa.String(length=16), nullable=False),
        sa.Column("actor_id", sa.String(length=96), nullable=False),
        sa.Column("account_ref", sa.String(length=64), nullable=True),
        sa.Column("tenant_ref", sa.String(length=64), nullable=False),
        sa.Column("product_ref", sa.String(length=64), nullable=False),
        sa.Column("cohort", sa.String(length=16), nullable=True),
        sa.Column("attribution", sa.String(length=16), nullable=True),
        sa.Column("result", sa.String(length=16), nullable=False, server_default="n/a"),
        sa.Column("error_class", sa.String(length=24), nullable=True),
        sa.Column("model_ref", sa.String(length=64), nullable=True),
        sa.Column("tokens_in", sa.Integer(), nullable=True),
        sa.Column("tokens_out", sa.Integer(), nullable=True),
        sa.Column("tokens_cached", sa.Integer(), nullable=True),
        sa.Column("work_unit_type", sa.String(length=24), nullable=True),
        sa.Column("work_units", sa.Integer(), nullable=True),
        sa.Column("est_cost_usd", sa.Float(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("cache_hit", sa.Boolean(), nullable=True),
        sa.Column("approval_gate", sa.String(length=48), nullable=True),
        sa.Column("decision", sa.String(length=16), nullable=True),
        sa.Column("decision_latency_ms", sa.Integer(), nullable=True),
        sa.Column("outcome_type", sa.String(length=32), nullable=True),
        sa.Column("outcome_value", sa.Integer(), nullable=True),
        sa.Column("handling_seconds", sa.Integer(), nullable=True),
    )
    op.create_index("ix_usage_events_event_type", "usage_events", ["event_type"])
    op.create_index("ix_usage_events_occurred_at", "usage_events", ["occurred_at"])
    op.create_index("ix_usage_events_workflow_type", "usage_events", ["workflow_type"])
    op.create_index("ix_usage_events_workflow_run_id", "usage_events", ["workflow_run_id"])
    op.create_index("ix_usage_events_account_ref", "usage_events", ["account_ref"])
    op.create_index("ix_usage_events_tenant_ref", "usage_events", ["tenant_ref"])
    op.create_index("ix_usage_events_product_ref", "usage_events", ["product_ref"])

    op.create_table(
        "usage_aggregates",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("day", sa.String(length=10), nullable=False),
        sa.Column("workflow_type", sa.String(length=48), nullable=False),
        sa.Column("tenant_ref", sa.String(length=64), nullable=False),
        sa.Column("product_ref", sa.String(length=64), nullable=False),
        sa.Column("cohort", sa.String(length=16), nullable=False, server_default=""),
        sa.Column("n_events", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metrics", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("day", "workflow_type", "tenant_ref", "product_ref", "cohort",
                            name="uq_usage_aggregate_group"),
    )
    op.create_index("ix_usage_aggregates_day", "usage_aggregates", ["day"])
    op.create_index("ix_usage_aggregates_tenant_ref", "usage_aggregates", ["tenant_ref"])

    op.create_table(
        "model_cost_rates",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("model_ref", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=48), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="USD"),
        sa.Column("rate_input_per_1k", sa.Float(), nullable=False, server_default="0"),
        sa.Column("rate_output_per_1k", sa.Float(), nullable=False, server_default="0"),
        sa.Column("rate_cached_input_per_1k", sa.Float(), nullable=False, server_default="0"),
        sa.Column("source_url", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("effective_date", sa.String(length=10), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_model_cost_rates_model_ref", "model_cost_rates", ["model_ref"], unique=True)


def downgrade():
    op.drop_table("model_cost_rates")
    op.drop_table("usage_aggregates")
    op.drop_table("usage_events")
