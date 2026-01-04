"""Add investment assets table.

Revision ID: 006_investment_assets
Revises: 005_user_settings
Create Date: 2025-01-15
"""
from alembic import op
import sqlalchemy as sa


revision = "006_investment_assets"
down_revision = "005_user_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type if it doesn't exist
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'investmentcategory') THEN
                CREATE TYPE investmentcategory AS ENUM ('rental', 'stocks', 'funds', 'crypto', 'portfolio', 'business', 'other');
            END IF;
        END
        $$;
        """
    )

    # Create table with raw SQL to avoid SQLAlchemy enum conflicts
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS investment_assets (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            category investmentcategory NOT NULL,
            current_value NUMERIC(18, 2) NOT NULL DEFAULT 0,
            currency VARCHAR(3) NOT NULL DEFAULT 'USD',
            notes VARCHAR(500),
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
        """
    )
    
    # Create indices
    op.execute("CREATE INDEX IF NOT EXISTS ix_investment_assets_id ON investment_assets(id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_investment_assets_user ON investment_assets(user_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS investment_assets CASCADE")
    op.execute("DROP TYPE IF EXISTS investmentcategory CASCADE")
