from __future__ import annotations

"""Extract class type parameters from ``typing.Generic`` bases."""

import typing as t
from typing import get_args, get_origin

from macrotype.modules.ir import ClassDecl, ModuleDecl, Site


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

    for m in sym.members:
        if isinstance(m, ClassDecl):
            inner = m.obj
            if isinstance(inner, type):
                _transform_class(m, inner)


def transform_generics(mi: ModuleDecl) -> None:
    """Attach class type parameters found in ``Generic`` bases."""

    for sym in mi.get_all_decls():
        if isinstance(sym, ClassDecl):
            cls = sym.obj
            if isinstance(cls, type):
                _transform_class(sym, cls)
