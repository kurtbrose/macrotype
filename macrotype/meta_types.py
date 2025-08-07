"""Helpers for dynamically created types."""

import sys
import typing
from collections import defaultdict
from contextlib import contextmanager
from types import UnionType
from typing import Any, Callable, Final

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


def overload_for(*args, **kwargs):
    """Decorator that records literal overload information for *args* and *kwargs*."""

    def decorator(func: Callable) -> Callable:
        result = func(*args, **kwargs)
        cases = getattr(func, "__overload_for__", [])
        cases.insert(0, (args, kwargs, result))
        func.__overload_for__ = cases
        return func

    return decorator


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
    "overload_for",
    "get_overloads",
    "clear_registry",
    "patch_typing",
    "all_annotations",
    "optional",
    "required",
    "pick",
    "omit",
    "final",
    "replace",
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


_NoneType = type(None)


def _make_class(name: str, annotations: dict[str, Any]) -> type:
    """Return a new class named *name* with *annotations*."""

    caller_mod = get_caller_module(3)

    @emit_as(name)
    class Generated:
        pass

    Generated.__annotations__ = annotations
    set_module(Generated, caller_mod)
    return Generated


def _strip_type(ann: Any, null: Any) -> Any:
    """Return *ann* with ``null`` removed from unions."""

    origin = typing.get_origin(ann)
    if origin in {typing.Union, UnionType}:
        args = [a for a in typing.get_args(ann) if a is not null]
        if not args:
            return null
        result = args[0]
        for a in args[1:]:
            result = result | a
        return result
    return ann


def all_annotations(cls: type) -> dict[str, Any]:
    """Return annotations from *cls* and all base classes."""
    out: dict[str, Any] = {}
    for base in reversed(cls.__mro__):
        out.update(getattr(base, "__annotations__", {}))
    return out


def optional(cls: type, *, null: Any = None) -> dict[str, Any]:
    """Return ``__annotations__`` of *cls* with all attributes made optional."""

    null_type = _NoneType if null is None else null
    return {k: v | null_type for k, v in all_annotations(cls).items()}


def required(cls: type, *, null: Any = None) -> dict[str, Any]:
    """Return ``__annotations__`` of *cls* with optional types made required."""

    null_type = _NoneType if null is None else null
    return {k: _strip_type(v, null_type) for k, v in all_annotations(cls).items()}


def pick(cls: type, keys: list[str]) -> dict[str, Any]:
    """Return ``__annotations__`` of *cls* containing only *keys*."""

    source = all_annotations(cls)
    return {k: source[k] for k in keys if k in source}


def omit(cls: type, keys: list[str]) -> dict[str, Any]:
    """Return ``__annotations__`` of *cls* with *keys* removed."""

    source = all_annotations(cls)
    return {k: v for k, v in source.items() if k not in keys}


def final(cls: type) -> dict[str, Any]:
    """Return ``__annotations__`` of *cls* with attributes wrapped in ``Final``."""

    return {k: Final[v] for k, v in all_annotations(cls).items()}


def replace(name: str, cls: type, mapping: dict[str, Any]) -> type:
    """Return a copy of *cls* with annotations updated from *mapping*."""

    anns = all_annotations(cls).copy()
    anns.update(mapping)
    return _make_class(name, anns)
