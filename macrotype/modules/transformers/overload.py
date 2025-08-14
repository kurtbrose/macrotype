from __future__ import annotations

"""Expand overloads and literal cases into multiple function symbols."""

import enum
import inspect
import types
import typing
from dataclasses import replace
from typing import Any, Callable

from macrotype.meta_types import get_overloads as _get_overloads
from macrotype.modules.scanner import _scan_function
from macrotype.modules.symbols import ClassSymbol, FuncSymbol, ModuleInfo, Symbol

# Helper copied from ``pyi_extract`` to synthesize literal overloads


def _annotation_for_value(value: Any) -> Any:
    if value is None:
        return type(None)
    if isinstance(value, enum.Enum):
        return typing.Literal[value]
    if isinstance(value, bool):
        return typing.Literal[value]
    if isinstance(value, (int, float, complex, str, bytes)) and not isinstance(value, bool):
        return typing.Literal[value]
    if isinstance(value, type):
        return value
    return type(value)


def _make_literal_overload(fn: Callable, args: tuple, kwargs: dict, result: Any) -> Callable:
    new_fn = types.FunctionType(
        fn.__code__, fn.__globals__, fn.__name__, fn.__defaults__, fn.__closure__
    )
    new_fn.__dict__.update(getattr(fn, "__dict__", {}))
    new_fn.__annotations__ = dict(getattr(fn, "__annotations__", {}))

    sig = inspect.signature(fn)
    bound = sig.bind_partial(*args, **kwargs)
    bound.apply_defaults()
    for name, value in bound.arguments.items():
        new_fn.__annotations__[name] = _annotation_for_value(value)
    new_fn.__annotations__["return"] = _annotation_for_value(result)
    return new_fn


def _expand_function(fn: Callable, sym: FuncSymbol) -> list[FuncSymbol]:
    ovs = _get_overloads(fn)
    cases = getattr(fn, "__overload_for__", [])
    if not ovs and not cases:
        return [sym]

    decos = sym.decorators + ("overload",)
    members: list[FuncSymbol] = []
    for ov in ovs:
        ov_sym = _scan_function(ov)
        ov_sym = replace(ov_sym, name=sym.name, decorators=decos)
        members.append(ov_sym)
    for args, kwargs, result in cases:
        case_fn = _make_literal_overload(fn, args, kwargs, result)
        case_sym = _scan_function(case_fn)
        case_sym = replace(case_sym, name=sym.name, decorators=decos)
        members.append(case_sym)
    if cases:
        members.append(replace(sym, decorators=decos))
    return members


def _get_function(cls: type | None, sym: FuncSymbol) -> Callable | None:
    if cls is None:
        return None
    attr = getattr(cls, sym.name, None)
    if attr is None:
        return None
    for deco in sym.decorators:
        if deco == "staticmethod" and isinstance(attr, staticmethod):
            return attr.__func__
        if deco == "classmethod" and isinstance(attr, classmethod):
            return attr.__func__
        if deco == "property" and isinstance(attr, property):
            return attr.fget
        if deco.endswith(".setter") and isinstance(attr, property):
            return attr.fset
        if deco.endswith(".deleter") and isinstance(attr, property):
            return attr.fdel
    if inspect.isfunction(attr):
        return attr
    return None


def _transform_class(sym: ClassSymbol, cls: type) -> None:
    members = list(sym.members)
    for i, m in enumerate(list(members)):
        if isinstance(m, FuncSymbol):
            fn = _get_function(cls, m)
            if fn is not None:
                expanded = _expand_function(fn, m)
                if expanded != [m]:
                    members[i : i + 1] = expanded
        elif isinstance(m, ClassSymbol):
            inner = getattr(cls, m.name, None)
            if isinstance(inner, type):
                _transform_class(m, inner)
    sym.members = tuple(members)


def expand_overloads(mi: ModuleInfo) -> None:
    """Expand overloads within ``mi`` into separate function symbols."""
    new_symbols: list[Symbol] = []
    for s in mi.symbols:
        match s:
            case FuncSymbol():
                fn_obj = getattr(mi.mod, s.name, None)
                if callable(fn_obj):
                    new_symbols.extend(_expand_function(fn_obj, s))
                else:
                    new_symbols.append(s)
            case ClassSymbol():
                cls = getattr(mi.mod, s.name, None)
                if isinstance(cls, type):
                    _transform_class(s, cls)
                new_symbols.append(s)
            case _:
                new_symbols.append(s)
    mi.symbols = new_symbols
