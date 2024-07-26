import asyncio

from alembic import context
from sqlalchemy import MetaData, engine_from_config, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

from src.utils.database import Base, SQLALCHEMY_URL, load_db_models
from src.utils.log import get_logger

# Obtain a custom logger instance
# This will also set up logging with our custom configuration
log = get_logger(__name__)

# Override the logging level of the alembic migration logs
# we set this to WARNING in the project to avoid log spam on auto-migrations
# however when alembic is ran manually, we want to see these logs, so set it
# back to the same level as the root log (INFO or DEBUG)
get_logger("alembic.runtime.migration").setLevel(get_logger().getEffectiveLevel())

# This is the Alembic Config object, which provides access to the values within the .ini file in use.
config = context.config


def run_migrations_offline(target_metadata: MetaData) -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the script output.
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


async def run_migrations_online(target_metadata: MetaData) -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection with the context.
    """

    def do_run_migrations(connection: Connection) -> None:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

    configuration = config.get_section(config.config_ini_section)
    if configuration is None:
        raise RuntimeError("Config ini section doesn't exists (should never happen)")

    connectable = AsyncEngine(
        engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def main() -> None:
    """Main entry point function."""
    config.set_main_option("sqlalchemy.url", SQLALCHEMY_URL)
    load_db_models()

    target_metadata = Base.metadata

    if context.is_offline_mode():
        run_migrations_offline(target_metadata)
    else:
        asyncio.run(run_migrations_online(target_metadata))


main()
