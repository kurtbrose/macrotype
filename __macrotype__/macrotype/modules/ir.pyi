# Generated via: macrotype macrotype/modules/ir.py -o __macrotype__/macrotype/modules/ir.pyi
# Do not edit by hand
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator, Literal

@dataclass(kw_only=True)
class Decl:
    name: str
    obj: EllipsisType | None | object
    comment: None | str
    emit: bool
    def get_children(self) -> tuple["Decl", ...]: ...
    def get_annotation_sites(self) -> tuple[Site, ...]: ...
    def walk(self) -> Iterator[Decl]: ...

@dataclass(kw_only=True)
class Site:
    role: Literal["var", "return", "param", "base", "alias_value", "td_field"]
    name: None | str
    index: None | int
    annotation: object
    comment: None | str

@dataclass(frozen=True, kw_only=True)
class AnnExpr:
    expr: str
    evaluated: Any

@dataclass(kw_only=True)
class VarDecl(Decl):
    site: Site
    obj: EllipsisType | None | object
    flags: dict[str, bool]  # final, classvar
    def get_annotation_sites(self) -> tuple[Site, ...]: ...

@dataclass(kw_only=True)
class FuncDecl(Decl):
    params: tuple[Site, ...]
    ret: None | Site
    obj: None | object
    decorators: tuple[str, ...]
    type_params: tuple[str, ...]
    flags: dict[str, bool]  # e.g., staticmethod, classmethod
    is_async: bool
    def get_annotation_sites(self) -> tuple[Site, ...]: ...

@dataclass(kw_only=True)
class ClassDecl(Decl):
    bases: tuple[Site, ...]
    td_fields: tuple[Site, ...]
    is_typeddict: bool
    td_total: None | bool
    members: tuple[Decl, ...]  # nested Var/Func/Class
    obj: None | object
    decorators: tuple[str, ...]
    flags: dict[str, bool]  # e.g., protocol, abstract
    type_params: tuple[str, ...]
    def get_children(self) -> tuple[Decl, ...]: ...
    def get_annotation_sites(self) -> tuple[Site, ...]: ...

@dataclass(kw_only=True)
class TypeDefDecl(Decl):
    value: None | Site
    obj: None | object
    type_params: tuple[str, ...]
    obj_type: None | object
    def get_annotation_sites(self) -> tuple[Site, ...]: ...

@dataclass(kw_only=True)
class SourceInfo:
    headers: list[str]
    comments: dict[int, str]
    line_map: dict[str, int]
    tc_imports: dict[str, set[str]]

@dataclass(kw_only=True)
class ImportBlock:
    typing: set[str]
    froms: dict[str, set[str]]
    def lines(self) -> list[str]: ...

@dataclass(kw_only=True)
class ModuleDecl(Decl):
    obj: ModuleType
    members: list[Decl]
    imports: ImportBlock
    source: None | SourceInfo
    def get_children(self) -> tuple[Decl, ...]: ...
    def iter_all_decls(self) -> Iterator[Decl]: ...
    def get_all_decls(self) -> list[Decl]: ...
