"""File containing a typed wrapper function around ``decouple.config``."""

from __future__ import annotations

from typing import Any, NewType, TYPE_CHECKING, TypeVar, cast, overload

from decouple import UndefinedValueError, config  # pyright: ignore[reportMissingTypeStubs]

if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = ["get_config"]

T = TypeVar("T")
U = TypeVar("U")
Sentinel = NewType("Sentinel", object)
_MISSING = cast(Sentinel, object())


@overload
def get_config(
    search_path: str,
    *,
    cast: None = None,
    default: U | Sentinel = _MISSING,
) -> str | U: ...


@overload
def get_config(
    search_path: str,
    *,
    cast: Callable[[str], T],
    default: U | Sentinel = _MISSING,
) -> T | U: ...


def get_config(
    search_path: str,
    *,
    cast: Callable[[str], object] | None = None,
    default: object = _MISSING,
) -> object:
    """Typed wrapper around ``decouple.config`` for static type analysis."""
    try:
        val = config(search_path)
    except UndefinedValueError as exc:
        if default is not _MISSING:
            return default
        raise exc from exc

    # Treat empty strings as unset values
    if val == "":
        if default is not _MISSING:
            return default

        raise UndefinedValueError(
            f"{search_path} was found, but the content was an empty string. "
            "Set a non-empty value for the envvar or define a default value."
        )

    # We run this again, this time with a cast function.
    # the reason we don't do this immediately is that the empty strings might not
    # work with the cast function, which could raise various exceptions.
    if cast is None:
        cast = lambda x: x
    return config(search_path, cast=cast)


@overload
def config_cast_list(cast: None = None) -> Callable[[str], list[str]]: ...


@overload
def config_cast_list(cast: Callable[[str], T]) -> Callable[[str], list[T]]: ...


def config_cast_list(cast: Callable[[str], object] | None = None) -> Callable[[str], list[Any]]:
    """Cast function to convert the content of an environmental variable to a list of values.

    This works by splitting the contents of the environmental variable on `,` characters.
    Currently, there is not support for escaping here, so list variables that require `,`
    symbol to be present will not work.

    You can use this function in :func:`get_config` for the ``cast`` argument.
    """
    if cast is None or cast is str:
        cast = lambda x: x

    def inner(raw_value: str) -> list[Any]:
        return [cast(x) for x in raw_value.split(",") if x]

    return inner
