"""Add onboarding profile for investor discovery.

Revision ID: 004_onboarding_profile
Revises: 003_strategy_engine
Create Date: 2024-01-16
"""
from alembic import op
import sqlalchemy as sa


revision = "004_onboarding_profile"
down_revision = "003_strategy_engine"
branch_labels = None
depends_on = None

riskappetite_enum = sa.Enum("low", "medium", "high", name="riskappetite")
investorprofile_enum = sa.Enum("conservative", "balanced", "growth", "active", name="investorprofile")


def upgrade() -> None:
    op.create_table(
        "onboarding_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("risk_appetite", riskappetite_enum, nullable=False),
        sa.Column("investor_profile", investorprofile_enum, nullable=False),
        sa.Column("goal_value", sa.Numeric(18, 2), nullable=False),
        sa.Column("goal_horizon_years", sa.Integer(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column("asset_allocation", sa.JSON(), nullable=False),
        sa.Column("investment_interests", sa.JSON(), nullable=False),
        sa.Column("vision", sa.String(length=500), nullable=True),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("user_id", name="uq_onboarding_user"),
    )
    op.create_index("ix_onboarding_profiles_id", "onboarding_profiles", ["id"])
    op.create_index("idx_onboarding_user", "onboarding_profiles", ["user_id"])


def downgrade() -> None:
    op.drop_index("idx_onboarding_user", table_name="onboarding_profiles")
    op.drop_index("ix_onboarding_profiles_id", table_name="onboarding_profiles")
    op.drop_table("onboarding_profiles")
    investorprofile_enum.drop(op.get_bind(), checkfirst=True)
    riskappetite_enum.drop(op.get_bind(), checkfirst=True)
