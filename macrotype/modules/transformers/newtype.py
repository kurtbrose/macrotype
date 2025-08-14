from __future__ import annotations

"""Convert typing.NewType functions into alias symbols."""

from typing import Any

from macrotype.modules.scanner import ModuleInfo
from macrotype.modules.symbols import (
    AliasSymbol,
    ClassSymbol,
    FuncSymbol,
    Site,
    Symbol,
    VarSymbol,
)


def _transform_symbols(symbols: list[Symbol], namespace: dict[str, Any]) -> list[Symbol]:
    new_syms: list[Symbol] = []
    for sym in symbols:
        match sym:
            case FuncSymbol(name=name, comment=comment, emit=emit):
                obj = namespace.get(name)
                if callable(obj) and hasattr(obj, "__supertype__"):
                    alias = AliasSymbol(
                        name=name,
                        value=Site(role="alias_value", annotation=obj.__supertype__),
                        alias_type=obj,
                        comment=comment,
                        emit=emit,
                    )
                    new_syms.append(alias)
                else:
                    new_syms.append(sym)
            case VarSymbol(name=name, comment=comment, emit=emit):
                obj = namespace.get(name)
                if callable(obj) and hasattr(obj, "__supertype__"):
                    alias = AliasSymbol(
                        name=name,
                        value=Site(role="alias_value", annotation=obj.__supertype__),
                        alias_type=obj,
                        comment=comment,
                        emit=emit,
                    )
                    new_syms.append(alias)
                else:
                    new_syms.append(sym)
            case ClassSymbol(name=name, members=members):
                obj = namespace.get(name)
                if isinstance(obj, type):
                    sym.members = tuple(_transform_symbols(list(members), vars(obj)))
                new_syms.append(sym)
            case _:
                new_syms.append(sym)
    return new_syms


def transform_newtypes(mi: ModuleInfo) -> None:
    """Replace typing.NewType callables in ``mi`` with alias symbols."""

    glb = vars(mi.mod)
    mi.symbols = _transform_symbols(mi.symbols, glb)
