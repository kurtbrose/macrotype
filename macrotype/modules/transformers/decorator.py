from __future__ import annotations

import functools
import inspect
from dataclasses import replace
from typing import Any, Callable

from macrotype.modules.ir import ModuleDecl, VarDecl
from macrotype.modules.scanner import _scan_function

_DEF_WRAPPER_TYPES = (
    classmethod,
    staticmethod,
    property,
    functools.cached_property,
)


def _unwrap_decorated_function(obj: Any) -> Callable | None:
    """Return the underlying function for *obj* if it is a wrapped callable."""
    while True:
        if inspect.isfunction(obj):
            return obj
        if not (
            callable(obj)
            and hasattr(obj, "__wrapped__")
            and inspect.isfunction(obj.__wrapped__)
            and not isinstance(obj, _DEF_WRAPPER_TYPES)
        ):
            return None
        obj = obj.__wrapped__


def unwrap_decorated_functions(mi: ModuleDecl) -> None:
    """Normalize wrapped callables in ``mi`` into function symbols."""
    new_members = []
    for sym in mi.members:
        if isinstance(sym, VarDecl):
            fn = _unwrap_decorated_function(sym.obj)
            if fn is not None:
                fn_sym = _scan_function(fn)
                fn_sym = replace(
                    fn_sym,
                    name=sym.name,
                    comment=sym.comment,
                    emit=sym.emit,
                )
                new_members.append(fn_sym)
                continue
        new_members.append(sym)
    mi.members = new_members
