import enum
import inspect
import types
import typing
from dataclasses import replace
from typing import Any, Callable

from macrotype.meta_types import get_overloads as _get_overloads
from macrotype.modules.ir import ClassDecl, Decl, FuncDecl, ModuleDecl
from macrotype.modules.scanner import _scan_function

# Helper to synthesize literal overloads


def _annotation_for_value(value: Any) -> Any:
    if value is None:
        return type(None)
    if isinstance(value, enum.Enum):
        return typing.Literal[value]
    if isinstance(value, bool):
        return typing.Literal[value]
    if isinstance(value, float):
        return float
    if isinstance(value, complex):
        return complex
    if isinstance(value, (int, str, bytes)) and not isinstance(value, bool):
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


def _expand_function(fn: Callable, sym: FuncDecl) -> list[FuncDecl]:
    ovs = _get_overloads(fn)
    cases = getattr(fn, "__overload_for__", [])
    if not ovs and not cases:
        return [sym]

    decos = sym.decorators + ("overload",)
    members: list[FuncDecl] = []
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


def _get_function(sym: FuncDecl) -> Callable | None:
    obj = sym.obj
    if callable(obj):
        return obj
    return None


def _transform_class(sym: ClassDecl) -> None:
    members = list(sym.members)
    for i, m in enumerate(list(members)):
        if isinstance(m, FuncDecl):
            fn = _get_function(m)
            if fn is not None:
                expanded = _expand_function(fn, m)
                if expanded != [m]:
                    members[i : i + 1] = expanded
    sym.members = tuple(members)


def expand_overloads(mi: ModuleDecl) -> None:
    """Expand overloads within ``mi`` into separate function symbols."""

    for sym in mi.get_all_decls():
        if isinstance(sym, ClassDecl):
            cls = sym.obj
            if isinstance(cls, type):
                _transform_class(sym)

    new_decls: list[Decl] = []
    for s in mi.members:
        if isinstance(s, FuncDecl):
            fn_obj = _get_function(s)
            if callable(fn_obj):
                new_decls.extend(_expand_function(fn_obj, s))
            else:
                new_decls.append(s)
        else:
            new_decls.append(s)
    mi.members = new_decls
