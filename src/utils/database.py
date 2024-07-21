import importlib
import pkgutil
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import NoReturn

from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.settings import ECHO_SQL, SQLITE_DATABASE_FILE
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


@asynccontextmanager
async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Obtain a database session."""
    async with SessionLocal() as session:
        yield session
