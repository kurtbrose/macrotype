from __future__ import annotations

"""Module analysis pipeline."""

import typing as t
from dataclasses import replace
from types import ModuleType

from ..types import from_type
from .emit import emit_module
from .scanner import ModuleInfo, scan_module
from .symbols import AliasSymbol, ClassSymbol, FuncSymbol, Site, Symbol, VarSymbol
from .validate import ModuleValidationError, validate


def from_module(glb_or_mod: ModuleType | t.Mapping[str, t.Any]) -> ModuleInfo:
    """Scan, type-check, and validate *glb_or_mod* into a ModuleInfo."""

    mi = scan_module(glb_or_mod)
    mi = _apply_types(mi)
    return validate(mi)


def _apply_types(mi: ModuleInfo) -> ModuleInfo:
    def conv_site(site: Site) -> Site:
        if site.ty is not None or site.raw is None:
            return site
        try:
            t = from_type(site.raw)
        except Exception:
            return site
        if getattr(t, "ty", None) is None:
            return site
        return replace(site, ty=t)

    def conv_sym(sym: Symbol) -> Symbol:
        match sym:
            case VarSymbol(site=site):
                return replace(sym, site=conv_site(site))
            case AliasSymbol(value=site):
                return replace(sym, value=conv_site(site) if site else None)
            case FuncSymbol(params=params, ret=ret):
                params_new = tuple(conv_site(p) for p in params)
                ret_new = conv_site(ret) if ret else None
                return replace(sym, params=params_new, ret=ret_new)
            case ClassSymbol(bases=bases, td_fields=fields, members=members):
                bases_new = tuple(conv_site(b) for b in bases)
                fields_new = tuple(conv_site(f) for f in fields)
                members_new = tuple(conv_sym(m) for m in members)
                return replace(
                    sym,
                    bases=bases_new,
                    td_fields=fields_new,
                    members=members_new,
                )
            case _:
                return sym

    syms_new = [conv_sym(s) for s in mi.symbols]
    return replace(mi, symbols=syms_new)


__all__ = [
    "ModuleInfo",
    "from_module",
    "emit_module",
    "scan_module",
    "validate",
    "ModuleValidationError",
]
