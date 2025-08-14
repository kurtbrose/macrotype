from __future__ import annotations

import typing as t

from macrotype.modules.ir import ClassDecl, ModuleDecl


def _transform_class(sym: ClassDecl, cls: type, td_meta: type) -> None:
    if isinstance(cls, td_meta):
        base_fields: set[str] = set()
        for base in cls.__mro__[1:]:
            if isinstance(base, td_meta):
                base_fields.update(getattr(base, "__annotations__", {}).keys())
        if base_fields:
            sym.td_fields = tuple(f for f in sym.td_fields if f.name not in base_fields)
            sym.td_total = None


def prune_inherited_typeddict_fields(mi: ModuleDecl) -> None:
    """Remove TypedDict fields shadowed by inherited bases within ``mi``."""
    td_meta = getattr(t, "_TypedDictMeta", ())
    for sym in mi.get_all_decls():
        if isinstance(sym, ClassDecl):
            cls = sym.obj
            if isinstance(cls, type):
                _transform_class(sym, cls, td_meta)
