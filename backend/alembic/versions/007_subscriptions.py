"""Add user subscriptions table.

Revision ID: 007_subscriptions
Revises: 006_investment_assets
Create Date: 2025-01-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "007_subscriptions"
down_revision = "006_investment_assets"
branch_labels = None
depends_on = None

subscriptionplan_enum = postgresql.ENUM(
    "starter",
    "pro",
    name="subscriptionplan",
    create_type=False,
)
subscriptionstatus_enum = postgresql.ENUM(
    "active",
    "trialing",
    "past_due",
    "canceled",
    "unpaid",
    "incomplete",
    "incomplete_expired",
    "paused",
    name="subscriptionstatus",
    create_type=False,
)


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'subscriptionplan') THEN
                CREATE TYPE subscriptionplan AS ENUM ('starter', 'pro');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'subscriptionstatus') THEN
                CREATE TYPE subscriptionstatus AS ENUM (
                    'active',
                    'trialing',
                    'past_due',
                    'canceled',
                    'unpaid',
                    'incomplete',
                    'incomplete_expired',
                    'paused'
                );
            END IF;
        END
        $$;
        """
    )

    op.create_table(
        "user_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan", subscriptionplan_enum, nullable=False, server_default="starter"),
        sa.Column("status", subscriptionstatus_enum, nullable=True),
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("stripe_price_id", sa.String(length=255), nullable=True),
        sa.Column("current_period_end", sa.DateTime(), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("user_id", name="uq_user_subscriptions_user"),
    )
    op.create_index("ix_user_subscriptions_id", "user_subscriptions", ["id"])
    op.create_index("idx_user_subscriptions_user", "user_subscriptions", ["user_id"])
    op.create_index("idx_user_subscriptions_customer", "user_subscriptions", ["stripe_customer_id"])
    op.create_index("idx_user_subscriptions_subscription", "user_subscriptions", ["stripe_subscription_id"])


def downgrade() -> None:
    op.drop_index("idx_user_subscriptions_subscription", table_name="user_subscriptions")
    op.drop_index("idx_user_subscriptions_customer", table_name="user_subscriptions")
    op.drop_index("idx_user_subscriptions_user", table_name="user_subscriptions")
    op.drop_index("ix_user_subscriptions_id", table_name="user_subscriptions")
    op.drop_table("user_subscriptions")
    op.execute("DROP TYPE IF EXISTS subscriptionstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS subscriptionplan CASCADE")
