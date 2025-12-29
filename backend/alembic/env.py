"""Alembic environment"""

import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Add parent directory to path so 'app' module can be found
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.user import Base
from app.models.account import Account  # noqa
from app.models.category import Category, CategoryRule  # noqa
from app.models.transaction import Transaction  # noqa
from app.models.budget import Budget  # noqa
from app.models.net_worth_snapshot import NetWorthSnapshot  # noqa
from app.models.auth import RefreshToken, PasswordResetToken, EmailVerificationToken  # noqa
from app.models.audit_log import AuditLog  # noqa
from app.models.notification import Notification  # noqa
from app.models.fx_rate import FXRate  # noqa
from app.models.job import Job  # noqa

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Model's MetaData for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Get the DATABASE_URL from environment variable
    database_url = os.getenv("DATABASE_URL", "").replace("+asyncpg", "")
    if not database_url:
        configuration = config.get_section(config.config_ini_section)
        database_url = configuration.get("sqlalchemy.url", "postgresql://localhost/finance_db") if configuration else "postgresql://localhost/finance_db"
    
    # Create config dict with the URL
    configuration = {"sqlalchemy.url": database_url}
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
