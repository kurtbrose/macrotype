from __future__ import annotations

import typing as t

from .scanner import ModuleInfo
from .symbols import ClassSymbol


def _transform_class(sym: ClassSymbol, cls: type, td_meta: type) -> None:
    if isinstance(cls, td_meta):
        base_fields: set[str] = set()
        for base in cls.__mro__[1:]:
            if isinstance(base, td_meta):
                base_fields.update(getattr(base, "__annotations__", {}).keys())
        if base_fields:
            sym.td_fields = tuple(f for f in sym.td_fields if f.name not in base_fields)
            sym.td_total = None
    for m in sym.members:
        if isinstance(m, ClassSymbol):
            inner = getattr(cls, m.name, None)
            if isinstance(inner, type):
                _transform_class(m, inner, td_meta)


def prune_inherited_typeddict_fields(mi: ModuleInfo) -> None:
    """Remove TypedDict fields shadowed by inherited bases within ``mi``."""
    td_meta = getattr(t, "_TypedDictMeta", ())
    for sym in mi.symbols:
        if isinstance(sym, ClassSymbol):
            cls = getattr(mi.mod, sym.name, None)
            if isinstance(cls, type):
                _transform_class(sym, cls, td_meta)
