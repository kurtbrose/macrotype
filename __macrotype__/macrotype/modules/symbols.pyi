# Generated via: macrotype macrotype/modules/symbols.py -o __macrotype__/macrotype/symbols.pyi
# Do not edit by hand
from dataclasses import dataclass
from typing import Literal

EllipsisType = ellipsis

@dataclass(kw_only=True)
class Symbol:
    name: str
    comment: None | str
    emit: bool

@dataclass(kw_only=True)
class Site:
    role: Literal['var', 'return', 'param', 'base', 'alias_value', 'td_field']
    name: None | str
    index: None | int
    annotation: object
    comment: None | str

@dataclass(kw_only=True)
class VarSymbol(Symbol):
    site: Site
    initializer: ellipsis | object
    flags: dict[str, bool]

@dataclass(kw_only=True)
class FuncSymbol(Symbol):
    params: tuple[Site, ...]
    ret: None | Site
    decorators: tuple[str, ...]
    flags: dict[str, bool]

@dataclass(kw_only=True)
class ClassSymbol(Symbol):
    bases: tuple[Site, ...]
    td_fields: tuple[Site, ...]
    is_typeddict: bool
    td_total: None | bool
    members: tuple[Symbol, ...]
    decorators: tuple[str, ...]
    flags: dict[str, bool]

@dataclass(kw_only=True)
class AliasSymbol(Symbol):
    value: None | Site
    type_params: tuple[str, ...]
    flags: dict[str, bool]
