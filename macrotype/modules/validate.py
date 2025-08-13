from __future__ import annotations

"""Validation for scanned modules."""

from dataclasses import replace

from ..types.ir import TyRoot
from .scanner import ModuleInfo
from .symbols import AliasSymbol, ClassSymbol, FuncSymbol, Site, Symbol, VarSymbol


class ModuleValidationError(TypeError):
    """Raised when a scanned module contains invalid constructs."""


def validate(mi: ModuleInfo) -> ModuleInfo:
    """Validate and return *mi*.

    The incoming ``ModuleInfo`` is expected to have ``TyRoot`` populated for
    each :class:`Site`.  This pass checks for context-sensitive flags such as
    ``ClassVar`` and ``Required``/``NotRequired`` and raises
    :class:`ModuleValidationError` if they are misused.
    """

    syms = [_validate_symbol(sym, in_class=False, in_td=False) for sym in mi.symbols]
    return replace(mi, symbols=syms)


def _validate_symbol(sym: Symbol, *, in_class: bool, in_td: bool) -> Symbol:
    match sym:
        case VarSymbol(site=site):
            site_v = _validate_site(site, in_class=in_class, in_td=in_td)
            return replace(sym, site=site_v)
        case AliasSymbol(value=site):
            site_v = _validate_site(site, in_class=in_class, in_td=in_td) if site else None
            return replace(sym, value=site_v)
        case FuncSymbol(params=params, ret=ret):
            params_v = tuple(_validate_site(p, in_class=in_class, in_td=in_td) for p in params)
            ret_v = _validate_site(ret, in_class=in_class, in_td=in_td) if ret else None
            return replace(sym, params=params_v, ret=ret_v)
        case ClassSymbol(bases=bases, td_fields=fields, is_typeddict=is_td, members=members):
            bases_v = tuple(_validate_site(b, in_class=in_class, in_td=in_td) for b in bases)
            fields_v = tuple(_validate_site(f, in_class=True, in_td=True) for f in fields)
            members_v = tuple(_validate_symbol(m, in_class=True, in_td=is_td) for m in members)
            return replace(
                sym,
                bases=bases_v,
                td_fields=fields_v,
                members=members_v,
            )
        case _:
            return sym


def _validate_site(site: Site, *, in_class: bool, in_td: bool) -> Site:
    ty = site.ty
    if isinstance(ty, TyRoot):
        if ty.is_classvar and not in_class:
            raise ModuleValidationError(f"ClassVar is only valid inside a class (at {site.role})")
        if ty.is_required is not None and not in_td:
            raise ModuleValidationError("Required/NotRequired is only valid for TypedDict fields")
        if in_td and ty.is_classvar:
            raise ModuleValidationError("ClassVar cannot be used in TypedDict fields")
    return site
