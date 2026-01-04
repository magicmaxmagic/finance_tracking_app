"""Add planning preferences to user settings.

Revision ID: 012_planning_preferences
Revises: 011_external_calendar_events
Create Date: 2025-02-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "012_planning_preferences"
down_revision = "011_external_calendar_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_settings",
        sa.Column("planning_preferences", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_settings", "planning_preferences")
