"""Initial migration - Create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-12-28 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_users_email', 'email'),
    )

    # Create accounts table
    op.create_table(
        'accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('account_type', postgresql.ENUM('cash', 'savings', 'checking', 'credit', 'investment', 'debt', 'other', name='accounttype'), nullable=False),
        sa.Column('currency', sa.String(3), default='USD'),
        sa.Column('balance', sa.Numeric(15, 2), default=0),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_accounts_user_id', 'user_id'),
    )

    # Create categories table
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('color', sa.String(7), default='#000000'),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('is_income', sa.Boolean(), default=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_categories_user_id', 'user_id'),
    )

    # Create category_rules table
    op.create_table(
        'category_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('rule_type', postgresql.ENUM('contains', 'regex', 'exact_match', name='ruletype'), nullable=False),
        sa.Column('pattern', sa.String(500), nullable=False),
        sa.Column('priority', sa.Integer(), default=0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('currency', sa.String(3), default='USD'),
        sa.Column('transaction_date', sa.DateTime(), nullable=False),
        sa.Column('tags', sa.String(500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_duplicate', sa.Boolean(), default=False),
        sa.Column('duplicate_of_id', sa.Integer(), nullable=True),
        sa.Column('import_id', sa.String(255), nullable=True, unique=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['duplicate_of_id'], ['transactions.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_transactions_user_date', 'user_id', 'transaction_date'),
        sa.Index('ix_transactions_account_date', 'account_id', 'transaction_date'),
        sa.Index('ix_transactions_category_date', 'category_id', 'transaction_date'),
        sa.Index('ix_transactions_import_id', 'import_id'),
    )

    # Create budgets table
    op.create_table(
        'budgets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('month', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_budgets_user_month', 'user_id', 'month'),
        sa.Index('ix_budgets_category_month', 'category_id', 'month'),
    )

    # Create net_worth_snapshots table
    op.create_table(
        'net_worth_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('balance', sa.Numeric(15, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_net_worth_user_date', 'user_id', 'snapshot_date'),
        sa.Index('ix_net_worth_account_date', 'account_id', 'snapshot_date'),
    )


def downgrade() -> None:
    op.drop_table('net_worth_snapshots')
    op.drop_table('budgets')
    op.drop_table('transactions')
    op.drop_table('category_rules')
    op.drop_table('categories')
    op.drop_table('accounts')
    op.drop_table('users')
    
    # Drop enums
    sa.Enum('cash', 'savings', 'checking', 'credit', 'investment', 'debt', 'other', name='accounttype').drop(op.get_bind())
    sa.Enum('contains', 'regex', 'exact_match', name='ruletype').drop(op.get_bind())
