"""Add user settings table.

Revision ID: 005_user_settings
Revises: 004_onboarding_profile
Create Date: 2024-01-16
"""
from alembic import op
import sqlalchemy as sa


revision = "005_user_settings"
down_revision = "004_onboarding_profile"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="America/New_York"),
        sa.Column("date_format", sa.String(length=24), nullable=False, server_default="MM/DD/YYYY"),
        sa.Column("start_of_week", sa.String(length=16), nullable=False, server_default="Monday"),
        sa.Column("default_view", sa.String(length=32), nullable=False, server_default="dashboard"),
        sa.Column("data_retention", sa.String(length=32), nullable=False, server_default="forever"),
        sa.Column("digest_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("transaction_alerts", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("budget_alerts", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("auto_categorization", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("import_deduplication", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("analytics_opt_in", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("user_id", name="uq_user_settings_user"),
    )
    op.create_index("ix_user_settings_id", "user_settings", ["id"])
    op.create_index("idx_user_settings_user", "user_settings", ["user_id"])


def downgrade() -> None:
    op.drop_index("idx_user_settings_user", table_name="user_settings")
    op.drop_index("ix_user_settings_id", table_name="user_settings")
    op.drop_table("user_settings")
