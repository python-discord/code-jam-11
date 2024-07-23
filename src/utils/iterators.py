from collections.abc import Iterator


def get_first[T, V](it: Iterator[T], default: V = None) -> T | V:
    """Get the first item from an iterable, or `default` if it's empty."""
    try:
        return next(it)
    except StopIteration:
        return default
