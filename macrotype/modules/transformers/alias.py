from __future__ import annotations

import sys
import types
import typing as t

from macrotype.modules.ir import ClassDecl, Decl, ModuleDecl, Site, TypeDefDecl, VarDecl
from macrotype.modules.transformers.generic import _format_type_param


def _transform_alias_vars(decls: list[Decl]) -> list[Decl]:
    """Convert ``VarDecl`` instances for TypeVar-like objects into ``TypeDefDecl``."""
    new_decls: list[Decl] = []
    for sym in decls:
        match sym:
            case VarDecl(name=name, obj=obj, comment=comment, emit=emit, site=site):
                if isinstance(obj, (t.TypeVar, t.ParamSpec, t.TypeVarTuple, types.GenericAlias)):
                    alias = TypeDefDecl(
                        name=name,
                        value=Site(role="alias_value", annotation=obj, comment=site.comment),
                        obj=obj,
                        comment=comment,
                        emit=emit,
                        obj_type=obj,
                    )
                    new_decls.append(alias)
                else:
                    new_decls.append(sym)
            case ClassDecl(members=members):
                sym.members = tuple(_transform_alias_vars(list(members)))
                new_decls.append(sym)
            case _:
                new_decls.append(sym)
    return new_decls


def synthesize_aliases(mi: ModuleDecl) -> None:
    """Normalize alias-like objects into ``TypeDefDecl`` instances."""
    glb = vars(mi.obj)
    annotations = glb.get("__annotations__", {}) or {}

    mi.members = _transform_alias_vars(mi.members)

    for sym in mi.get_all_decls():
        if not isinstance(sym, TypeDefDecl):
            continue
        obj = sym.obj
        if isinstance(obj, t.TypeAliasType):  # type: ignore[attr-defined]
            sym.value = Site(role="alias_value", annotation=obj.__value__)
            sym.obj_type = obj
            params: list[str] = []
            for tp in getattr(obj, "__type_params__", ()):  # pragma: no cover - py312+
                if sys.version_info >= (3, 13):
                    params.append(_format_type_param(tp))
                elif isinstance(tp, t.ParamSpec):
                    params.append(f"**{tp.__name__}")
                elif isinstance(tp, t.TypeVarTuple):
                    params.append(f"*{tp.__name__}")
                else:
                    params.append(tp.__name__)
            sym.type_params = tuple(params)
        elif annotations.get(sym.name) is t.TypeAlias:
            sym.obj_type = t.TypeAlias
        elif isinstance(obj, (t.TypeVar, t.ParamSpec, t.TypeVarTuple, types.GenericAlias)):
            sym.obj_type = obj
