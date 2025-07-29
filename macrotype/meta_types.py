"""Helpers for dynamically created types."""

import sys
import typing
from collections import defaultdict
from contextlib import contextmanager
from typing import Any, Callable

_OVERLOAD_REGISTRY: dict[str, dict[str, list[Callable]]] = defaultdict(lambda: defaultdict(list))

_ORIG_GET_OVERLOADS = getattr(typing, "get_overloads", lambda func: [])
_ORIG_OVERLOAD = typing.overload


def overload(func: Callable) -> Callable:
    """Replacement ``overload`` decorator that also registers with ``typing``."""
    _OVERLOAD_REGISTRY[func.__module__][func.__qualname__].append(func)
    try:
        func = _ORIG_OVERLOAD(func)
    except Exception:
        pass
    return func


def get_overloads(func: Callable) -> list[Callable]:
    """Return overloads registered for *func* including builtin ones."""
    f = getattr(func, "__func__", func)
    qualname = getattr(f, "__overload_name__", getattr(f, "__qualname_override__", f.__qualname__))
    ours = list(_OVERLOAD_REGISTRY[f.__module__][qualname])
    orig = list(_ORIG_GET_OVERLOADS(f))
    all_ovs = ours + [ov for ov in orig if ov not in ours]
    return all_ovs


def clear_registry() -> None:
    """Remove all registered overloads and clear ``typing``'s registry."""
    _OVERLOAD_REGISTRY.clear()
    clear = getattr(typing, "clear_overloads", None)
    if clear is not None:
        try:
            clear()
        except Exception:
            pass


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


__all__ = [
    "emit_as",
    "set_module",
    "get_caller_module",
    "make_literal_map",
    "overload",
    "get_overloads",
    "clear_registry",
    "patch_typing",
]


def get_caller_module(level: int = 2) -> str:
    """Return the name of the module ``level`` calls up the stack."""
    frame = sys._getframe(level)
    return frame.f_globals.get("__name__", "__main__")


def set_module(obj: Any, module: str) -> None:
    """Set ``obj.__module__`` to *module* and adjust overloads."""
    old_mod = getattr(obj, "__module__", None)
    try:
        obj.__module__ = module
    except Exception:
        return

    dct = getattr(obj, "__dict__", {})
    for attr in list(dct.values()):
        if callable(attr):
            try:
                attr.__module__ = module
            except Exception:
                pass

    if old_mod and old_mod != module:
        old_overloads = _OVERLOAD_REGISTRY.get(old_mod)
        if old_overloads:
            prefix = getattr(obj, "__qualname_override__", getattr(obj, "__name__", "")) + "."
            for key in list(old_overloads.keys()):
                if key.startswith(prefix):
                    _OVERLOAD_REGISTRY[module][key] = old_overloads.pop(key)


def emit_as(name: str):
    """Decorator that overrides the emitted name for a function or class."""

    def set_qualname(obj: Any):
        obj.__qualname_override__ = name

        mod_overloads = _OVERLOAD_REGISTRY.get(obj.__module__)
        if mod_overloads:
            old_prefix = obj.__qualname__ + "."
            new_prefix = name + "."
            for key in list(mod_overloads.keys()):
                if key.startswith(old_prefix):
                    funcs = mod_overloads.pop(key)
                    new_key = new_prefix + key[len(old_prefix) :]
                    mod_overloads[new_key] = funcs
                    method_name = key[len(old_prefix) :].split(".", 1)[0]
                    attr = getattr(obj, method_name, None)
                    if callable(attr):
                        setattr(attr, "__overload_name__", new_key)
                    for ov in funcs:
                        setattr(ov, "__overload_name__", new_key)

        return obj

    return set_qualname


def make_literal_map(name: str, mapping: dict[str | int, str | int]):
    """Dynamically build a class exposing ``mapping`` via ``Literal`` overloads."""

    caller_mod = get_caller_module()

    @emit_as(name)
    class LiteralMap:
        for k, v in mapping.items():

            @typing.overload  # type: ignore[misc]
            def __getitem__(self, key: typing.Literal[k]) -> typing.Literal[v]: ...

        def __getitem__(self, key):
            return mapping[key]

    set_module(LiteralMap, caller_mod)

    return LiteralMap
