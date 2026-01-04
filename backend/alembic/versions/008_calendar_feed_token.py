"""Add calendar feed token to user settings.

Revision ID: 008_calendar_feed_token
Revises: 007_subscriptions
Create Date: 2025-02-10
"""
from alembic import op
import sqlalchemy as sa


revision = "008_calendar_feed_token"
down_revision = "007_subscriptions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_settings", sa.Column("calendar_feed_token", sa.String(length=128), nullable=True))
    op.create_index(
        "idx_user_settings_calendar_feed_token",
        "user_settings",
        ["calendar_feed_token"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("idx_user_settings_calendar_feed_token", table_name="user_settings")
    op.drop_column("user_settings", "calendar_feed_token")
