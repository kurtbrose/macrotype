# Generated via: macrotype macrotype
# Do not edit by hand
from dataclasses import dataclass
from macrotype.types.ir import Provenance, Ty
from typing import Literal

EllipsisType = ellipsis

@dataclass(frozen=True, kw_only=True)
class Symbol:
    name: str
    key: str
    prov: None | Provenance

@dataclass(frozen=True, kw_only=True)
class Site:
    role: Literal['var', 'return', 'param', 'base', 'alias_value', 'td_field']
    name: None | str
    index: None | int
    raw: object
    ty: None | Ty

@dataclass(frozen=True, kw_only=True)
class VarSymbol(Symbol):
    site: Site
    initializer: ellipsis | object
    flags: dict[str, bool]

@dataclass(frozen=True, kw_only=True)
class FuncSymbol(Symbol):
    params: tuple[Site, ...]
    ret: None | Site
    decorators: tuple[str, ...]
    overload_index: None | int
    flags: dict[str, bool]

@dataclass(frozen=True, kw_only=True)
class ClassSymbol(Symbol):
    bases: tuple[Site, ...]
    td_fields: tuple[Site, ...]
    is_typeddict: bool
    td_total: None | bool
    members: tuple[Symbol, ...]
    flags: dict[str, bool]

@dataclass(frozen=True, kw_only=True)
class AliasSymbol(Symbol):
    value: None | Site
