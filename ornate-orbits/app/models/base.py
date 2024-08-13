from collections.abc import Callable, Sequence
from typing import Any

from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase


class classproperty:  # noqa: N801
    """Decorator that converts a method.

    with a single cls argument into a property
    that can be accessed directly from the class.
    """

    def __init__(self, method: Callable[..., Any]) -> None:
        self.fget = method

    def __get__(self, instance: Any, cls: type) -> Any:  # noqa: ANN401
        return self.fget(cls)

    def getter(self, method: Callable[..., Any]) -> "classproperty":
        """Return the method."""
        self.fget = method
        return self


class Base(DeclarativeBase):
    """Base model."""

    @classproperty
    def relationships(cls) -> Sequence[str]:  # noqa: N805
        """Return all relationship columns."""
        return cls.__mapper__.relationships.keys()

    @classproperty
    def columns(cls) -> Sequence[str]:  # noqa: N805
        """Return all columns."""
        return [column.key for column in inspect(cls).mapper.attrs]

    def as_dict(self) -> dict[str, Any]:
        """Return dictionary format."""
        return {
            col.key: getattr(self, col.key)
            for col in inspect(self).mapper.column_attrs
        }
