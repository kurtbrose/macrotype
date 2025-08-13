# Generated via: macrotype macrotype
# Do not edit by hand
from dataclasses import dataclass
from types import EllipsisType
from typing import Literal

@dataclass(frozen=True, kw_only=True)
class Symbol:
    name: str

@dataclass(frozen=True, kw_only=True)
class Site:
    role: Literal["var", "return", "param", "base", "alias_value", "td_field"]
    name: None | str
    index: None | int
    annotation: object

@dataclass(frozen=True, kw_only=True)
class VarSymbol(Symbol):
    site: Site
    initializer: EllipsisType | object
    flags: dict[str, bool]

@dataclass(frozen=True, kw_only=True)
class FuncSymbol(Symbol):
    params: tuple[Site, ...]
    ret: None | Site
    decorators: tuple[str, ...]
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
