"""
migrations/env.py
-----------------
Alembic environment configured for async SQLAlchemy + asyncpg.

Key points:
  - DATABASE_URL is read from Settings (env var) — never hardcoded.
  - Inside Docker the DATABASE_URL env var is set by docker-compose.yml
    to use the internal `db:5432` hostname, not localhost.
  - compare_type=True so autogenerate detects column type changes.
  - compare_server_default=True so server-side defaults are tracked.
"""

from __future__ import annotations

import asyncio
import re
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.models import Base  # noqa: F401  — registers all ORM models

settings = get_settings()
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline mode (generate SQL without connecting)
# ---------------------------------------------------------------------------


def run_migrations_offline() -> None:
    """
    Run migrations without an active DB connection.
    Useful for generating raw SQL to review before applying.
    """
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online mode (connect and apply)
# ---------------------------------------------------------------------------


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = create_async_engine(
        settings.database_url,
        poolclass=pool.NullPool,  # No pooling during migrations
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
