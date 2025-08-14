"""Normalize NamedTuple classes."""

from __future__ import annotations

import typing as t

from macrotype.modules.symbols import ClassSymbol, ModuleInfo, Site, VarSymbol


def _transform_class(sym: ClassSymbol, cls: type) -> None:
    if issubclass(cls, tuple) and hasattr(cls, "_fields"):
        field_names = set(getattr(cls, "_fields", ()))
        sym.members = tuple(
            m for m in sym.members if isinstance(m, VarSymbol) and m.name in field_names
        )
        new_bases: list[Site] = [Site(role="base", annotation=t.NamedTuple)]
        for b in sym.bases:
            ann = b.annotation
            if getattr(ann, "__name__", None) == "NamedTuple":
                continue
            new_bases.append(b)
        sym.bases = tuple(new_bases)
    for m in sym.members:
        if isinstance(m, ClassSymbol):
            inner = getattr(cls, m.name, None)
            if isinstance(inner, type):
                _transform_class(m, inner)


def transform_namedtuples(mi: ModuleInfo) -> None:
    """Convert NamedTuple classes in ``mi`` to standard form."""

    for sym in mi.get_all_symbols():
        if isinstance(sym, ClassSymbol):
            cls = getattr(mi.mod, sym.name, None)
            if isinstance(cls, type):
                _transform_class(sym, cls)
