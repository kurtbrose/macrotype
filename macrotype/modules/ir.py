from __future__ import annotations

from dataclasses import dataclass, field
from types import EllipsisType, ModuleType
from typing import Iterator, Literal, Optional


@dataclass(kw_only=True)
class Decl:
    """Base class for all top-level or nested declarations."""

    name: str
    obj: object | EllipsisType | None = None
    comment: str | None = None
    emit: bool = True

    def get_children(self) -> tuple["Decl", ...]:
        return ()

    def get_annotation_sites(self) -> tuple[Site, ...]:
        return ()

    def walk(self) -> Iterator["Decl"]:
        yield self
        for child in self.get_children():
            yield from child.walk()


@dataclass(kw_only=True)
class Site:
    role: Literal["var", "return", "param", "base", "alias_value", "td_field"]
    name: Optional[str] = None
    index: Optional[int] = None
    annotation: object = None
    comment: str | None = None


@dataclass(kw_only=True)
class VarDecl(Decl):
    site: Site
    obj: object | EllipsisType | None = None
    flags: dict[str, bool] = field(default_factory=dict)  # final, classvar

    def get_annotation_sites(self) -> tuple[Site, ...]:
        return (self.site,)


@dataclass(kw_only=True)
class FuncDecl(Decl):
    params: tuple[Site, ...]
    ret: Optional[Site]
    obj: object | None = None
    decorators: tuple[str, ...] = ()
    flags: dict[str, bool] = field(default_factory=dict)  # e.g., staticmethod, classmethod

    def get_annotation_sites(self) -> tuple[Site, ...]:
        sites = list(self.params)
        if self.ret is not None:
            sites.append(self.ret)
        return tuple(sites)


@dataclass(kw_only=True)
class ClassDecl(Decl):
    bases: tuple[Site, ...]
    td_fields: tuple[Site, ...] = ()
    is_typeddict: bool = False
    td_total: Optional[bool] = None
    members: tuple[Decl, ...] = ()  # nested Var/Func/Class
    obj: object | None = None
    decorators: tuple[str, ...] = ()
    flags: dict[str, bool] = field(default_factory=dict)  # e.g., protocol, abstract

    def get_children(self) -> tuple[Decl, ...]:
        return self.members

    def get_annotation_sites(self) -> tuple[Site, ...]:
        return self.bases + self.td_fields


@dataclass(kw_only=True)
class AliasDecl(Decl):
    value: Optional[Site]
    obj: object | None = None
    type_params: tuple[str, ...] = ()
    alias_type: object | None = None

    def get_annotation_sites(self) -> tuple[Site, ...]:
        return (self.value,) if self.value is not None else ()


@dataclass(kw_only=True)
class ModuleDecl(Decl):
    obj: ModuleType
    members: list[Decl]

    def get_children(self) -> tuple[Decl, ...]:
        return tuple(self.members)

    def iter_all_decls(self) -> Iterator[Decl]:
        for decl in self.members:
            yield from decl.walk()

    def get_all_decls(self) -> list[Decl]:
        return list(self.iter_all_decls())
