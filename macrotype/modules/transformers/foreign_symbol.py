from __future__ import annotations

import typing as t

from macrotype.modules.ir import AliasDecl, Decl, ModuleDecl, Site, VarDecl


def canonicalize_foreign_symbols(mi: ModuleDecl) -> None:
    """Replace variables referencing foreign objects with aliases."""

    glb = vars(mi.obj)
    modname = mi.obj.__name__
    annotations: dict[str, t.Any] = glb.get("__annotations__", {}) or {}
    new_syms: list[Decl] = []
    for sym in mi.members:
        if not isinstance(sym, VarDecl):
            new_syms.append(sym)
            continue
        obj = sym.obj
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
                    AliasDecl(
                        name=sym.name,
                        value=Site(role="alias_value", annotation=obj),
                        obj=obj,
                        comment=sym.comment,
                        emit=sym.emit,
                    )
                )
            continue
        new_syms.append(sym)
    mi.members = new_syms
