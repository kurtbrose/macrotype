"""Normalize NamedTuple classes."""

from __future__ import annotations

import typing as t

from macrotype.modules.ir import ClassDecl, ModuleDecl, Site, VarDecl


def _transform_class(sym: ClassDecl, cls: type) -> None:
    if issubclass(cls, tuple) and hasattr(cls, "_fields"):
        field_names = set(getattr(cls, "_fields", ()))
        sym.members = tuple(
            m for m in sym.members if isinstance(m, VarDecl) and m.name in field_names
        )
        new_bases: list[Site] = [Site(role="base", annotation=t.NamedTuple)]
        for b in sym.bases:
            ann = b.annotation
            if getattr(ann, "__name__", None) == "NamedTuple":
                continue
            new_bases.append(b)
        sym.bases = tuple(new_bases)
    for m in sym.members:
        if isinstance(m, ClassDecl):
            inner = m.obj
            if isinstance(inner, type):
                _transform_class(m, inner)


def transform_namedtuples(mi: ModuleDecl) -> None:
    """Convert NamedTuple classes in ``mi`` to standard form."""

    for sym in mi.get_all_decls():
        if isinstance(sym, ClassDecl):
            cls = sym.obj
            if isinstance(cls, type):
                _transform_class(sym, cls)
