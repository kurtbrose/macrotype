from __future__ import annotations

"""Normalize ``final``/``override``/``abstract`` flags on symbols."""

import inspect
from typing import Any

from macrotype.modules.ir import ClassDecl, FuncDecl, ModuleDecl


def _normalize_function(sym: FuncDecl, fn: Any, *, is_method: bool) -> None:
    """Attach flag information for *fn* to ``sym``."""

    flags = sym.flags
    decos = list(sym.decorators)

    if getattr(fn, "__final__", False):
        flags["final"] = True
        if is_method:
            decos.append("final")
    if getattr(fn, "__override__", False):
        flags["override"] = True
        if is_method:
            decos.append("override")
    if getattr(fn, "__isabstractmethod__", False):
        flags["abstract"] = True
        if is_method:
            decos.append("abstractmethod")

    norm: list[str] = []
    seen: set[str] = set()
    for deco in decos:
        base = deco.split(".")[-1]
        if base == "final":
            flags["final"] = True
            if is_method and base not in seen:
                norm.append("final")
                seen.add("final")
        elif base == "override":
            flags["override"] = True
            if base not in seen:
                norm.append("override")
                seen.add("override")
        elif base == "abstractmethod":
            flags["abstract"] = True
            if is_method and base not in seen:
                norm.append("abstractmethod")
                seen.add("abstractmethod")
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
        elif isinstance(m, ClassDecl):
            inner = m.obj
            if isinstance(inner, type):
                _normalize_class(m, inner)


def normalize_flags(mi: ModuleDecl) -> None:
    """Attach ``final``/``override``/``abstract`` flags to symbols in ``mi``."""

    for sym in mi.members:
        if isinstance(sym, FuncDecl):
            fn = sym.obj
            if callable(fn):
                _normalize_function(sym, fn, is_method=False)
        elif isinstance(sym, ClassDecl):
            cls = sym.obj
            if isinstance(cls, type):
                _normalize_class(sym, cls)
