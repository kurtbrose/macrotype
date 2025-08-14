from __future__ import annotations

import typing as t

from .scanner import ModuleInfo
from .symbols import AliasSymbol, Site, Symbol, VarSymbol


def canonicalize_foreign_symbols(mi: ModuleInfo) -> None:
    """Replace variables referencing foreign objects with aliases."""

    glb = vars(mi.mod)
    modname = mi.mod.__name__
    annotations: dict[str, t.Any] = glb.get("__annotations__", {}) or {}
    new_syms: list[Symbol] = []
    for sym in mi.symbols:
        if not isinstance(sym, VarSymbol):
            new_syms.append(sym)
            continue
        obj = glb.get(sym.name, sym.initializer)
        if obj is Ellipsis:
            new_syms.append(sym)
            continue
        if not hasattr(obj, "__module__"):
            if sym.name in annotations or isinstance(obj, (int, str, float, bool)):
                new_syms.append(sym)
            continue
        if obj.__module__ != modname:
            if sym.name in annotations or isinstance(obj, (int, str, float, bool)):
                new_syms.append(sym)
                continue
            alias_name = getattr(obj, "__name__", None)
            if alias_name and alias_name != sym.name:
                new_syms.append(
                    AliasSymbol(
                        name=sym.name,
                        value=Site(role="alias_value", annotation=obj),
                        comment=sym.comment,
                        emit=sym.emit,
                    )
                )
            continue
        new_syms.append(sym)
    mi.symbols = new_syms
