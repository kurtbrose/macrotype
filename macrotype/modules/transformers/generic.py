from __future__ import annotations

"""Extract type parameters for classes and functions."""

import typing as t
from typing import Callable, get_args, get_origin

from macrotype.modules.ir import ClassDecl, FuncDecl, ModuleDecl, Site
from macrotype.types_ast import find_typevars


def _format_type_param(param: t.Any) -> str:
    origin = get_origin(param)
    if origin is t.Unpack:
        (inner,) = get_args(param)
        if isinstance(inner, t.TypeVarTuple):
            return f"*{inner.__name__}"
        if isinstance(inner, t.ParamSpec):
            return f"**{inner.__name__}"
        if isinstance(inner, t.TypeVar):
            return f"*{inner.__name__}"
        return f"*{getattr(inner, '__name__', repr(inner))}"
    if isinstance(param, t.TypeVarTuple):
        return f"*{param.__name__}"
    if isinstance(param, t.ParamSpec):
        return f"**{param.__name__}"
    if isinstance(param, t.TypeVar):
        return param.__name__
    return getattr(param, "__name__", repr(param))


def _transform_class(sym: ClassDecl, cls: type) -> None:
    type_params: list[str] = []
    new_bases: list[Site] = []
    for b in sym.bases:
        ann = b.annotation
        if get_origin(ann) is t.Generic:
            for param in get_args(ann):
                type_params.append(_format_type_param(param))
            continue
        new_bases.append(b)

    if type_params:
        sym.type_params = tuple(type_params)
        sym.bases = tuple(new_bases)


def _transform_function(sym: FuncDecl, fn: Callable, enclosing: tuple[str, ...] = ()) -> None:
    tp_objs = getattr(fn, "__type_params__", None)
    if tp_objs:
        sym.type_params = tuple(_format_type_param(tp) for tp in tp_objs)
        return
    try:
        hints = t.get_type_hints(fn, include_extras=True)
    except Exception:
        hints = getattr(fn, "__annotations__", {}) or {}
    annots = list(hints.values())
    if annots:
        params = sorted(set().union(*(find_typevars(a) for a in annots)))
        sym.type_params = tuple(p for p in params if p not in enclosing)


def transform_generics(mi: ModuleDecl) -> None:
    """Attach type parameters to classes and functions within ``mi``."""

    def walk(sym, enclosing: tuple[str, ...] = ()) -> None:
        match sym:
            case ClassDecl():
                cls = sym.obj
                if isinstance(cls, type):
                    _transform_class(sym, cls)
                for mem in sym.members:
                    walk(mem, enclosing + sym.type_params)
            case FuncDecl():
                fn = sym.obj
                if callable(fn):
                    _transform_function(sym, fn, enclosing)

    for sym in mi.members:
        walk(sym)
