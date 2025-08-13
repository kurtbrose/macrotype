from __future__ import annotations

from dataclasses import dataclass, field
from types import EllipsisType
from typing import Literal, Optional


@dataclass(kw_only=True)
class Symbol:
    """Base class for all top-level or nested declarations."""

    name: str
    comment: str | None = None


@dataclass(kw_only=True)
class Site:
    role: Literal["var", "return", "param", "base", "alias_value", "td_field"]
    name: Optional[str] = None
    index: Optional[int] = None
    annotation: object
    comment: str | None = None


@dataclass(kw_only=True)
class VarSymbol(Symbol):
    site: Site
    initializer: object | EllipsisType = Ellipsis
    flags: dict[str, bool] = field(default_factory=dict)  # final, classvar


@dataclass(kw_only=True)
class FuncSymbol(Symbol):
    params: tuple[Site, ...]
    ret: Optional[Site]
    decorators: tuple[str, ...] = ()
    flags: dict[str, bool] = field(default_factory=dict)  # e.g., staticmethod, classmethod


@dataclass(kw_only=True)
class ClassSymbol(Symbol):
    bases: tuple[Site, ...]
    td_fields: tuple[Site, ...] = ()
    is_typeddict: bool = False
    td_total: Optional[bool] = None
    members: tuple[Symbol, ...] = ()  # nested Var/Func/Class
    decorators: tuple[str, ...] = ()
    flags: dict[str, bool] = field(default_factory=dict)  # e.g., protocol, abstract


@dataclass(kw_only=True)
class AliasSymbol(Symbol):
    value: Optional[Site]
