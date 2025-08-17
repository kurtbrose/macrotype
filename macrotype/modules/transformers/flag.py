from __future__ import annotations

"""Normalize ``final``/``override``/``abstract`` flags on symbols."""

import inspect
from typing import Any

from macrotype.modules.ir import ClassDecl, FuncDecl, ModuleDecl


def _normalize_function(sym: FuncDecl, fn: Any, *, is_method: bool) -> None:
    """Attach flag information for *fn* to ``sym``."""

    flags = sym.flags
    decos = list(sym.decorators)

    # Insert ``final``/``override``/``abstractmethod`` before any descriptor
    # decorators (``classmethod``, ``staticmethod``, ``property``) so that the
    # emitted order matches conventional usage, e.g. ``@override`` appearing
    # before ``@classmethod``.  ``inspect`` does not preserve the original
    # decorator order for these flags, so we reconstruct it here.
    def _insert(deco: str) -> None:
        if not is_method:
            return
        descriptor_pos = next(
            (i for i, d in enumerate(decos) if d in {"classmethod", "staticmethod", "property"}),
            len(decos),
        )
        if deco not in decos:
            decos.insert(descriptor_pos, deco)

    if getattr(fn, "__final__", False):
        flags["final"] = True
        _insert("final")
    if getattr(fn, "__override__", False):
        flags["override"] = True
        _insert("override")
    if getattr(fn, "__isabstractmethod__", False):
        flags["abstract"] = True
        _insert("abstractmethod")

    norm: list[str] = []
    seen: set[str] = set()
    for deco in decos:
        base = deco.split(".")[-1]
        if base in {"final", "override", "abstractmethod"}:
            if base not in seen:
                norm.append(base)
                seen.add(base)
        else:
            if deco not in seen:
                norm.append(deco)
                seen.add(deco)
    sym.decorators = tuple(norm)


def _normalize_class(sym: ClassDecl, cls: type) -> None:
    flags = sym.flags
    decos = list(sym.decorators)

    if getattr(cls, "__final__", False):
        flags["final"] = True
        decos.append("final")
    if inspect.isabstract(cls):
        flags["abstract"] = True

    norm: list[str] = []
    seen: set[str] = set()
    for deco in decos:
        base = deco.split(".")[-1]
        if base == "final":
            flags["final"] = True
            if base not in seen:
                norm.append("final")
                seen.add("final")
        else:
            if deco not in seen:
                norm.append(deco)
                seen.add(deco)
    sym.decorators = tuple(norm)

    for m in sym.members:
        if isinstance(m, FuncDecl):
            fn = m.obj
            if callable(fn):
                _normalize_function(m, fn, is_method=True)


def normalize_flags(mi: ModuleDecl) -> None:
    """Attach ``final``/``override``/``abstract`` flags to symbols in ``mi``."""

    for sym in mi.members:
        if isinstance(sym, FuncDecl):
            fn = sym.obj
            if callable(fn):
                _normalize_function(sym, fn, is_method=False)

    for sym in mi.get_all_decls():
        if isinstance(sym, ClassDecl):
            cls = sym.obj
            if isinstance(cls, type):
                _normalize_class(sym, cls)
