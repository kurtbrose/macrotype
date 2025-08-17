from __future__ import annotations

"""Extract type parameters for classes and functions."""

import typing as t
from typing import Callable, get_args, get_origin

from macrotype.modules.ir import ClassDecl, FuncDecl, ModuleDecl, Site
from macrotype.types.ir import (
    TyApp,
    TyCallable,
    TyParamSpec,
    TyTypeVar,
    TyTypeVarTuple,
    TyUnion,
    TyUnpack,
)
from macrotype.types.parse import parse_root


def _format_type_param(param: t.Any) -> str:
    """Return a string representation for ``param``."""

    origin = get_origin(param)
    if origin is t.Unpack:
        (inner,) = get_args(param)
        text = _format_type_param(inner)
        return text if text.startswith("*") else f"*{text}"

    default = getattr(param, "__default__", None)
    if default in {t.Any, (), None}:
        default = None
    if isinstance(param, t.TypeVar):
        if param.__constraints__ and default not in param.__constraints__:
            default = None
    if isinstance(param, t.TypeVarTuple):
        if default is not None and not isinstance(default, (tuple, t.TypeVarTuple)):
            default = None
    if isinstance(param, t.ParamSpec):
        if default is not None and not isinstance(default, (tuple, t.ParamSpec)):
            default = None

    if isinstance(param, t.TypeVarTuple):
        text = f"*{param.__name__}"
        if default is not None:
            if isinstance(default, tuple):
                items = ", ".join(_format_type_param(d) for d in default)
                text += f" = ({items})"
            else:
                text += f" = {_format_type_param(default)}"
        return text

    if isinstance(param, t.ParamSpec):
        text = f"**{param.__name__}"
        if default is not None:
            if isinstance(default, tuple):
                items = ", ".join(_format_type_param(d) for d in default)
                text += f" = ({items})"
            else:
                text += f" = {_format_type_param(default)}"
        return text

    if isinstance(param, t.TypeVar):
        name = param.__name__
        text = name
        if param.__bound__ is not None:
            text += f": {_format_type_param(param.__bound__)}"
        elif param.__constraints__:
            items = ", ".join(_format_type_param(c) for c in param.__constraints__)
            text += f": ({items})"
        if default is not None:
            text += f" = {_format_type_param(default)}"
        return text

    name = getattr(param, "__qualname__", getattr(param, "__name__", None))
    mod = getattr(param, "__module__", "")
    if name is None:
        text = repr(param)
    elif mod in {"typing", "builtins", ""}:
        text = name
    else:
        text = f"{mod}.{name}"
    if default is not None:
        text += f" = {_format_type_param(default)}"
    return text


def _find_typevars(obj: t.Any) -> set[str]:
    """Return the set of type variable names used in ``obj``."""

    root = parse_root(obj)
    found: set[str] = set()

    def visit(node):
        if node is None:
            return
        match node:
            case TyTypeVar(name=n):
                found.add(n)
            case TyParamSpec(name=n):
                found.add(f"**{n}")
            case TyTypeVarTuple(name=n):
                found.add(f"*{n}")
            case TyApp(base=b, args=args):
                visit(b)
                for a in args:
                    visit(a)
            case TyUnion(options=opts):
                for o in opts:
                    visit(o)
            case TyCallable(params=ps, ret=r):
                if ps is not Ellipsis:
                    for p in ps:
                        visit(p)
                visit(r)
            case TyUnpack(inner=i):
                visit(i)
            case _:
                pass

    visit(root.ty)
    return found


def _transform_class(sym: ClassDecl, cls: type) -> None:
    tp_objs = getattr(cls, "__type_params__", None)
    if tp_objs:
        sym.type_params = tuple(_format_type_param(tp) for tp in tp_objs)
        sym.bases = tuple(b for b in sym.bases if get_origin(b.annotation) is not t.Generic)
        return

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
        params = sorted(set().union(*(_find_typevars(a) for a in annots)))
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
