from __future__ import annotations

"""Infer parameter types from default values."""

import inspect
from typing import Callable

from macrotype.modules.ir import ClassDecl, FuncDecl, ModuleDecl, Site


def _infer_function(sym: FuncDecl, fn: Callable) -> None:
    sig = inspect.signature(fn)
    existing = {p.name.lstrip("*"): p for p in sym.params}
    new_params: list[Site] = []
    for p in sig.parameters.values():
        name = p.name
        if p.kind is inspect.Parameter.VAR_POSITIONAL:
            display = f"*{name}"
        elif p.kind is inspect.Parameter.VAR_KEYWORD:
            display = f"**{name}"
        else:
            display = name
        site = existing.get(name)
        if site is not None:
            if site.name != display:
                site = Site(role="param", name=display, annotation=site.annotation)
        else:
            ann = None
            if (
                p.default is not inspect._empty
                and p.default is not None
                and name not in {"self", "cls"}
            ):
                ann = type(p.default)
            site = Site(role="param", name=display, annotation=ann)
        new_params.append(site)
    sym.params = tuple(new_params)


def _transform_class(sym: ClassDecl, cls: type) -> None:
    for m in sym.members:
        if isinstance(m, FuncDecl):
            fn = m.obj
            if callable(fn):
                _infer_function(m, fn)
        elif isinstance(m, ClassDecl):
            inner = m.obj
            if isinstance(inner, type):
                _transform_class(m, inner)


def infer_param_defaults(mi: ModuleDecl) -> None:
    """Infer parameter types from default values within ``mi``."""
    for sym in mi.members:
        if isinstance(sym, FuncDecl):
            fn = sym.obj
            if callable(fn):
                _infer_function(sym, fn)
        elif isinstance(sym, ClassDecl):
            cls = sym.obj
            if isinstance(cls, type):
                _transform_class(sym, cls)
