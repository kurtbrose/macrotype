from __future__ import annotations

import typing as t

from macrotype.modules.scanner import ModuleInfo
from macrotype.modules.symbols import AliasSymbol, Site


def synthesize_aliases(mi: ModuleInfo) -> None:
    """Normalize alias-like objects into AliasSymbol instances."""
    glb = vars(mi.mod)
    annotations = glb.get("__annotations__", {}) or {}
    for sym in mi.symbols:
        if not isinstance(sym, AliasSymbol):
            continue
        obj = glb.get(sym.name)
        if isinstance(obj, t.TypeAliasType):  # type: ignore[attr-defined]
            sym.value = Site(role="alias_value", annotation=obj.__value__)
            sym.alias_type = obj
            params: list[str] = []
            for tp in getattr(obj, "__type_params__", ()):  # pragma: no cover - py312+
                if glb.get(tp.__name__) is tp:
                    if isinstance(tp, t.ParamSpec):
                        params.append(f"**{tp.__name__}")
                    elif isinstance(tp, t.TypeVarTuple):
                        params.append(f"*{tp.__name__}")
                    else:
                        params.append(tp.__name__)
                else:
                    params.append(tp.__name__)
            sym.type_params = tuple(params)
        elif annotations.get(sym.name) is t.TypeAlias:
            sym.alias_type = t.TypeAlias
        elif isinstance(obj, (t.TypeVar, t.ParamSpec, t.TypeVarTuple)):
            sym.alias_type = obj
