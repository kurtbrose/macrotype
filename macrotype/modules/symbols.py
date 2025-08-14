from __future__ import annotations

from dataclasses import dataclass, field
from types import EllipsisType, ModuleType
from typing import Iterator, Literal, Optional


@dataclass(kw_only=True)
class Symbol:
    """Base class for all top-level or nested declarations."""

    name: str
    comment: str | None = None
    emit: bool = True

    def get_children(self) -> tuple["Symbol", ...]:
        return ()

    def get_annotation_sites(self) -> tuple[Site, ...]:
        return ()

    def walk(self) -> Iterator["Symbol"]:
        yield self
        for child in self.get_children():
            yield from child.walk()


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

    def get_annotation_sites(self) -> tuple[Site, ...]:
        return (self.site,)


@dataclass(kw_only=True)
class FuncSymbol(Symbol):
    params: tuple[Site, ...]
    ret: Optional[Site]
    decorators: tuple[str, ...] = ()
    flags: dict[str, bool] = field(default_factory=dict)  # e.g., staticmethod, classmethod

    def get_annotation_sites(self) -> tuple[Site, ...]:
        sites = list(self.params)
        if self.ret is not None:
            sites.append(self.ret)
        return tuple(sites)


@dataclass(kw_only=True)
class ClassSymbol(Symbol):
    bases: tuple[Site, ...]
    td_fields: tuple[Site, ...] = ()
    is_typeddict: bool = False
    td_total: Optional[bool] = None
    members: tuple[Symbol, ...] = ()  # nested Var/Func/Class
    decorators: tuple[str, ...] = ()
    flags: dict[str, bool] = field(default_factory=dict)  # e.g., protocol, abstract

    def get_children(self) -> tuple[Symbol, ...]:
        return self.members

    def get_annotation_sites(self) -> tuple[Site, ...]:
        return self.bases + self.td_fields


@dataclass(kw_only=True)
class AliasSymbol(Symbol):
    value: Optional[Site]
    type_params: tuple[str, ...] = ()
    alias_type: object | None = None

    def get_annotation_sites(self) -> tuple[Site, ...]:
        return (self.value,) if self.value is not None else ()


@dataclass
class ModuleInfo:
    """Scanned representation of a Python module."""

    mod: ModuleType
    symbols: list[Symbol]

    def iter_all_symbols(self) -> Iterator[Symbol]:
        for sym in self.symbols:
            yield from sym.walk()

    def get_all_symbols(self) -> list[Symbol]:
        return list(self.iter_all_symbols())
