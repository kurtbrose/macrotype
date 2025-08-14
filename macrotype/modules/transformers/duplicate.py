from __future__ import annotations

from macrotype.modules.ir import Decl, ModuleDecl, Site, TypeDefDecl


def canonicalize_local_aliases(mi: ModuleDecl) -> None:
    """Replace duplicate variables referencing local objects with aliases."""

    modname = mi.obj.__name__
    seen: dict[int, str] = {}
    new_syms: list[Decl] = []
    for sym in mi.members:
        obj = getattr(sym, "obj", None)
        obj_mod = getattr(obj, "__module__", None)
        if obj is None or obj_mod != modname:
            new_syms.append(sym)
            continue
        obj_id = id(obj)
        if obj_id in seen:
            canonical = seen[obj_id]
            if canonical != sym.name:
                new_syms.append(
                    TypeDefDecl(
                        name=sym.name,
                        value=Site(role="alias_value", annotation=obj),
                        obj=obj,
                        comment=getattr(sym, "comment", None),
                        emit=getattr(sym, "emit", True),
                    )
                )
            continue
        seen[obj_id] = sym.name
        new_syms.append(sym)
    mi.members = new_syms
