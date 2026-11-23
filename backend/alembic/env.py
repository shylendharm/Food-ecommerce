"""
Alembic Runtime Environment Configuration
Location: backend/alembic/env.py

Binds Alembic to our FastAPI application's SQLAlchemy metadata
and dynamically injects the MySQL connection URL from .env.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# -------------------------------------------------------------
# 1. Ensure backend/ is in Python's search path
# -------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# -------------------------------------------------------------
# 2. Import application database Base metadata and models
# -------------------------------------------------------------
from app.database import Base, DATABASE_URL
import app.models  # Guarantees all 6 tables are registered in Base.metadata!

# Alembic Config object, providing access to values in alembic.ini
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# -------------------------------------------------------------
# 3. Dynamic Configuration Injection (No hardcoded credentials!)
# -------------------------------------------------------------
# Injects our live DATABASE_URL from .env directly into Alembic
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Sets the target metadata that Alembic will inspect for 'autogenerate'
target_metadata = Base.metadata


# -------------------------------------------------------------
# 4. Migration Execution Modes
# -------------------------------------------------------------

def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    Emits raw SQL to stdout without requiring an active database connection.
    """
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
    """
    Run migrations in 'online' mode.
    Connects directly to MySQL and applies schema migrations inside a transaction.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()