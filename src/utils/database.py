import importlib
import pkgutil
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import NoReturn

import alembic.config
from alembic.operations import Operations
from alembic.runtime.environment import EnvironmentContext
from alembic.runtime.migration import MigrationContext, RevisionStep
from alembic.script import ScriptDirectory
from sqlalchemy import Connection
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.settings import DB_ALWAYS_MIGRATE, ECHO_SQL, SQLITE_DATABASE_FILE
from src.utils.log import get_logger

log = get_logger(__name__)

__all__ = ["engine", "Base", "load_db_models", "get_db_session"]

SQLALCHEMY_URL = f"sqlite+aiosqlite:///{SQLITE_DATABASE_FILE.absolute()}"
TABLES_PACKAGE_PATH = "src.db_tables"


engine = create_async_engine(SQLALCHEMY_URL, echo=ECHO_SQL)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    """SQLAlchemy base class for registering ORM models.

    Note: Before calling ``Base.metadata.create_all``, all models that inherit
    from this class must already be loaded (imported), so that this metaclass
    can know about all of the models. See :func:`load_models`.
    """


def load_db_models() -> None:
    """Import all models (all files/modules containing the models).

    This step is required before calling ``Base.metadata.create_all``, as all models
    need to first be imported, so that they get registered into the :class:`Base` class.
    """

    def on_error(name: str) -> NoReturn:
        """Handle an error encountered while walking packages."""
        raise ImportError(name=name)

    def ignore_module(module: pkgutil.ModuleInfo) -> bool:
        """Return whether the module with name `name` should be ignored."""
        return any(name.startswith("_") for name in module.name.split("."))

    log.debug(f"Loading database modules from {TABLES_PACKAGE_PATH}")
    db_module = importlib.import_module(TABLES_PACKAGE_PATH)
    for module_info in pkgutil.walk_packages(db_module.__path__, f"{db_module.__name__}.", onerror=on_error):
        if ignore_module(module_info):
            continue

        log.debug(f"Loading database module: {module_info.name}")
        importlib.import_module(module_info.name)


def apply_db_migrations(db_conn: Connection) -> None:
    """Apply alembic database migrations.

    This method will first check if the database is empty (no applied alembic revisions),
    in which case, it use SQLAlchemy to create all tables and then stamp the database for alembic.

    If the database is not empty, it will apply all necessary migrations, bringing the database
    up to date with the latest revision.
    """
    # Create a standalone minimal config, that doesn't use alembic.ini
    # (we don't want to load env.py, since they do a lot of things we don't want
    # like setting up logging in a different way, ...)
    alembic_cfg = alembic.config.Config()
    alembic_cfg.set_main_option("script_location", "alembic-migrations")
    alembic_cfg.set_main_option("sqlalchemy.url", SQLALCHEMY_URL)

    script = ScriptDirectory.from_config(alembic_cfg)

    def retrieve_migrations(rev: str, context: MigrationContext) -> list[RevisionStep]:
        """Retrieve all remaining migrations to be applied to get to "head".

        The returned migrations will be the migrations that will get applied when upgrading.
        """
        migrations = script._upgrade_revs("head", rev)  # pyright: ignore[reportPrivateUsage]

        if len(migrations) > 0:
            log.info(f"Applying {len(migrations)} database migrations")
        else:
            log.debug("No database migrations to apply, database is up to date")

        return migrations

    env_context = EnvironmentContext(alembic_cfg, script)
    env_context.configure(connection=db_conn, target_metadata=Base.metadata, fn=retrieve_migrations)
    context = env_context.get_context()

    current_rev = context.get_current_revision()

    # If there is no current revision, this is a brand new database
    # instead of going through the migrations, we can instead use metadata.create_all
    # to create all tables and then stamp the database with the head revision.
    if current_rev is None and not DB_ALWAYS_MIGRATE:
        log.info("Performing initial database setup (creating tables)")
        Base.metadata.create_all(db_conn)
        context.stamp(script, "head")
        return

    log.debug("Checking for database migrations")
    with Operations.context(context) as _op, context.begin_transaction():
        context.run_migrations()


@asynccontextmanager
async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Obtain a database session."""
    async with SessionLocal() as session:
        yield session
