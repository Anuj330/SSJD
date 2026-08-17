import sys
import os

from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context


from dotenv import load_dotenv
load_dotenv()

from app.core.database import Base, engine
from app.models import user, society, members, member_profile, location, member_account, ledger, scheme, deposit, loan, share, activity_log, payment

# 🔥 IMPORTANT: Import all models here so Alembic detects them
# -----------------------------
# Alembic Config
# -----------------------------
config = context.config

# Use DATABASE_URL from .env instead of hardcoded alembic.ini value
database_url = os.environ.get("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# -----------------------------
# Offline Migrations
# -----------------------------
def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# -----------------------------
# Online Migrations
# -----------------------------
def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# -----------------------------
# Run Mode
# -----------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
