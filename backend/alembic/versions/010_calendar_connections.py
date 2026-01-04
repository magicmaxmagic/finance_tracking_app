"""Add calendar connections table.

Revision ID: 010_calendar_connections
Revises: 009_schedule_blocks
Create Date: 2025-02-10
"""
from alembic import op
import sqlalchemy as sa


revision = "010_calendar_connections"
down_revision = "009_schedule_blocks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "calendar_connections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("account_email", sa.String(length=255), nullable=False),
        sa.Column("calendar_name", sa.String(length=255), nullable=True),
        sa.Column("calendar_url", sa.String(length=512), nullable=True),
        sa.Column("encrypted_secret", sa.String(length=1024), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("user_id", "provider", name="uq_calendar_connections_user_provider"),
    )
    op.create_index("ix_calendar_connections_id", "calendar_connections", ["id"])
    op.create_index("idx_calendar_connections_user", "calendar_connections", ["user_id"])
    op.create_index("idx_calendar_connections_provider", "calendar_connections", ["provider"])


def downgrade() -> None:
    op.drop_index("idx_calendar_connections_provider", table_name="calendar_connections")
    op.drop_index("idx_calendar_connections_user", table_name="calendar_connections")
    op.drop_index("ix_calendar_connections_id", table_name="calendar_connections")
    op.drop_table("calendar_connections")
