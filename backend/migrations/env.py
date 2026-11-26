
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

import app.models  # noqa: F401
from app.core.config import settings
from app.db.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_database_url() -> str:
    arguments = context.get_x_argument(as_dictionary=True)

    if arguments.get("test") == "true":
        if not settings.test_database_url:
            raise RuntimeError(
                "TEST_DATABASE_URL must be configured."
            )

        from sqlalchemy.engine import make_url

        database = make_url(settings.test_database_url).database

        if database != "caterflow_test":
            raise RuntimeError(
                "Alembic test migrations can only run "
                "against 'caterflow_test'."
            )

        return settings.test_database_url

    return settings.database_url


def run_migrations_offline() -> None:
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(
        get_database_url(),
        pool_pre_ping=True,
    )

    try:
        with engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
                compare_server_default=True,
            )

            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
