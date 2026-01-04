"""Add strategy engine models for goals, assumptions, and scenarios.

Revision ID: 003_strategy_engine
Revises: 002_auth_notifications_fx_jobs
Create Date: 2024-01-15
"""
from alembic import op
import sqlalchemy as sa


revision = "003_strategy_engine"
down_revision = "002_auth_notifications_fx_jobs"
branch_labels = None
depends_on = None


goaltype_enum = sa.Enum("net_worth", "liquid_assets", name="goaltype")
goalstatus_enum = sa.Enum("active", "achieved", "archived", name="goalstatus")
risklevel_enum = sa.Enum("low", "medium", "high", name="risklevel")
actiontype_enum = sa.Enum(
    "income_delta",
    "expense_delta",
    "investment_delta",
    "one_time_investment",
    name="actiontype",
)


def upgrade() -> None:
    op.create_table(
        "financial_goals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("target_type", goaltype_enum, nullable=False),
        sa.Column("target_value", sa.Numeric(18, 2), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column("status", goalstatus_enum, nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_financial_goals_id", "financial_goals", ["id"])
    op.create_index("idx_goal_user_status", "financial_goals", ["user_id", "status"])
    op.create_index("idx_goal_user_target", "financial_goals", ["user_id", "target_date"])

    op.create_table(
        "assumption_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("income_growth_rate", sa.Numeric(6, 3), nullable=False, server_default="0"),
        sa.Column("expense_inflation_rate", sa.Numeric(6, 3), nullable=False, server_default="0"),
        sa.Column("investment_return_rate", sa.Numeric(6, 3), nullable=False, server_default="0"),
        sa.Column("volatility", sa.Numeric(6, 3), nullable=False, server_default="0"),
        sa.Column("risk_level", risklevel_enum, nullable=False, server_default="medium"),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("user_id", "version", name="uq_assumption_version_user"),
    )
    op.create_index("ix_assumption_versions_id", "assumption_versions", ["id"])
    op.create_index("idx_assumption_user_active", "assumption_versions", ["user_id", "is_active"])

    op.create_table(
        "scenarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("goal_id", sa.Integer(), sa.ForeignKey("financial_goals.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assumption_id", sa.Integer(), sa.ForeignKey("assumption_versions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("scenario_group_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_baseline", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("scenario_group_id", "version", name="uq_scenario_group_version"),
    )
    op.create_index("ix_scenarios_id", "scenarios", ["id"])
    op.create_index("idx_scenario_user_active", "scenarios", ["user_id", "is_active"])

    op.create_table(
        "scenario_actions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scenario_id", sa.Integer(), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action_type", actiontype_enum, nullable=False),
        sa.Column("value", sa.Numeric(15, 2), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_scenario_actions_id", "scenario_actions", ["id"])
    op.create_index("idx_action_scenario", "scenario_actions", ["scenario_id"])


def downgrade() -> None:
    op.drop_index("idx_action_scenario", table_name="scenario_actions")
    op.drop_index("ix_scenario_actions_id", table_name="scenario_actions")
    op.drop_table("scenario_actions")

    op.drop_index("idx_scenario_user_active", table_name="scenarios")
    op.drop_index("ix_scenarios_id", table_name="scenarios")
    op.drop_table("scenarios")

    op.drop_index("idx_assumption_user_active", table_name="assumption_versions")
    op.drop_index("ix_assumption_versions_id", table_name="assumption_versions")
    op.drop_table("assumption_versions")

    op.drop_index("idx_goal_user_target", table_name="financial_goals")
    op.drop_index("idx_goal_user_status", table_name="financial_goals")
    op.drop_index("ix_financial_goals_id", table_name="financial_goals")
    op.drop_table("financial_goals")

    actiontype_enum.drop(op.get_bind(), checkfirst=True)
    risklevel_enum.drop(op.get_bind(), checkfirst=True)
    goalstatus_enum.drop(op.get_bind(), checkfirst=True)
    goaltype_enum.drop(op.get_bind(), checkfirst=True)
