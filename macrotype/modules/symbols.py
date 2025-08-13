from __future__ import annotations

from dataclasses import dataclass, field
from types import EllipsisType
from typing import Literal, Optional

from ..types.ir import TyRoot


@dataclass(frozen=True)
class Provenance:
    """Non-semantic source info (for diagnostics), e.g. module/file/line."""

    module: str
    qualname: str
    file: Optional[str] = None
    line: Optional[int] = None


@dataclass(frozen=True, kw_only=True)
class Symbol:
    """Base class for all top-level or nested declarations."""

    name: str
    key: str  # e.g. "mymod.MyClass.__init__"
    prov: Optional[Provenance] = field(default=None, compare=False, hash=False, repr=False)


@dataclass(frozen=True, kw_only=True)
class Site:
    role: Literal["var", "return", "param", "base", "alias_value", "td_field"]
    name: Optional[str] = None
    index: Optional[int] = None
    raw: object
    ty: Optional[TyRoot] = None
    prov: Optional[Provenance] = field(default=None, compare=False, hash=False, repr=False)


@dataclass(frozen=True, kw_only=True)
class VarSymbol(Symbol):
    site: Site
    initializer: object | EllipsisType = Ellipsis
    flags: dict[str, bool] = field(default_factory=dict)  # final, classvar


@dataclass(frozen=True, kw_only=True)
class FuncSymbol(Symbol):
    params: tuple[Site, ...]
    ret: Optional[Site]
    decorators: tuple[str, ...] = ()
    overload_index: Optional[int] = None
    flags: dict[str, bool] = field(default_factory=dict)  # e.g., staticmethod, classmethod


@dataclass(frozen=True, kw_only=True)
class ClassSymbol(Symbol):
    bases: tuple[Site, ...]
    td_fields: tuple[Site, ...] = ()
    is_typeddict: bool = False
    td_total: Optional[bool] = None
    members: tuple[Symbol, ...] = ()  # nested Var/Func/Class
    flags: dict[str, bool] = field(default_factory=dict)  # e.g., protocol, abstract


@dataclass(frozen=True, kw_only=True)
class AliasSymbol(Symbol):
    value: Optional[Site]
