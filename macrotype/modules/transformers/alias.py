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
        if annotations.get(sym.name) is t.TypeAlias:
            sym.flags["is_typealias"] = True
        if isinstance(obj, t.TypeVar):
            sym.flags["is_typevar"] = True
        elif isinstance(obj, t.ParamSpec):
            sym.flags["is_paramspec"] = True
        elif isinstance(obj, t.TypeVarTuple):
            sym.flags["is_typevartuple"] = True
