from __future__ import annotations

from collections import defaultdict
from contextlib import contextmanager
import typing
from typing import Callable


# Registry of overload implementations indexed by module and qualified name
_OVERLOAD_REGISTRY: dict[str, dict[str, list[Callable]]] = defaultdict(lambda: defaultdict(list))

# Original functions so we can delegate when needed
_ORIG_GET_OVERLOADS = getattr(typing, "get_overloads", lambda func: [])
_ORIG_OVERLOAD = typing.overload


def overload(func: Callable) -> Callable:
    """Replacement ``overload`` decorator using a list registry."""
    _OVERLOAD_REGISTRY[func.__module__][func.__qualname__].append(func)
    return func


def get_overloads(func: Callable) -> list[Callable]:
    """Return overloads registered for *func* including builtin ones."""
    f = getattr(func, "__func__", func)
    ours = _OVERLOAD_REGISTRY[f.__module__][f.__qualname__]
    return _ORIG_GET_OVERLOADS(f) + list(ours)


def clear_registry() -> None:
    """Remove all registered overloads."""
    _OVERLOAD_REGISTRY.clear()


@contextmanager
def patch_typing():
    """Context manager that patches ``typing.overload`` and ``get_overloads``."""

    orig_overload = typing.overload
    orig_get = getattr(typing, "get_overloads", None)
    clear_registry()
    typing.overload = overload
    typing.get_overloads = get_overloads
    try:
        yield
    finally:
        typing.overload = orig_overload
        if orig_get is not None:
            typing.get_overloads = orig_get

