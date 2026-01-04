"""Add external calendar events table.

Revision ID: 011_external_calendar_events
Revises: 010_calendar_connections
Create Date: 2025-02-10
"""
from alembic import op
import sqlalchemy as sa


revision = "011_external_calendar_events"
down_revision = "010_calendar_connections"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "external_calendar_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False, server_default="ics"),
        sa.Column("calendar_name", sa.String(length=255), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=True),
        sa.Column("summary", sa.String(length=255), nullable=True),
        sa.Column("starts_at", sa.DateTime(), nullable=False),
        sa.Column("ends_at", sa.DateTime(), nullable=False),
        sa.Column("is_all_day", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_external_calendar_events_id", "external_calendar_events", ["id"])
    op.create_index("idx_external_events_user", "external_calendar_events", ["user_id"])
    op.create_index("idx_external_events_provider", "external_calendar_events", ["provider"])
    op.create_index("idx_external_events_source", "external_calendar_events", ["source"])
    op.create_index("idx_external_events_start", "external_calendar_events", ["starts_at"])


def downgrade() -> None:
    op.drop_index("idx_external_events_start", table_name="external_calendar_events")
    op.drop_index("idx_external_events_source", table_name="external_calendar_events")
    op.drop_index("idx_external_events_provider", table_name="external_calendar_events")
    op.drop_index("idx_external_events_user", table_name="external_calendar_events")
    op.drop_index("ix_external_calendar_events_id", table_name="external_calendar_events")
    op.drop_table("external_calendar_events")
