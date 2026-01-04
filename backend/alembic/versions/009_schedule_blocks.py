"""Add schedule blocks table.

Revision ID: 009_schedule_blocks
Revises: 008_calendar_feed_token
Create Date: 2025-02-10
"""
from alembic import op
import sqlalchemy as sa


revision = "009_schedule_blocks"
down_revision = "008_calendar_feed_token"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "schedule_blocks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("category", sa.String(length=32), nullable=False, server_default="FINANCE"),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_schedule_blocks_id", "schedule_blocks", ["id"])
    op.create_index("idx_schedule_blocks_user", "schedule_blocks", ["user_id"])
    op.create_index("idx_schedule_blocks_user_day", "schedule_blocks", ["user_id", "day_of_week"])


def downgrade() -> None:
    op.drop_index("idx_schedule_blocks_user_day", table_name="schedule_blocks")
    op.drop_index("idx_schedule_blocks_user", table_name="schedule_blocks")
    op.drop_index("ix_schedule_blocks_id", table_name="schedule_blocks")
    op.drop_table("schedule_blocks")
