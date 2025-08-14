from __future__ import annotations

import typing as t

from macrotype.modules.ir import AliasDecl, ModuleDecl, Site


def synthesize_aliases(mi: ModuleDecl) -> None:
    """Normalize alias-like objects into AliasDecl instances."""
    glb = vars(mi.obj)
    annotations = glb.get("__annotations__", {}) or {}
    for sym in mi.get_all_decls():
        if not isinstance(sym, AliasDecl):
            continue
        obj = sym.obj
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
