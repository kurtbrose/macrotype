from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal

EllipsisType = ellipsis

ModuleType = module

@dataclass(kw_only=True)
class Decl:
    name: str
    obj: None | ellipsis | object
    comment: None | str
    emit: bool
    def get_children(self) -> tuple[Decl, ...]: ...
    def get_annotation_sites(self) -> tuple[Site, ...]: ...
    def walk(self) -> Iterator[Decl]: ...

@dataclass(kw_only=True)
class Site:
    role: Literal["var", "return", "param", "base", "alias_value", "td_field"]
    name: None | str
    index: None | int
    annotation: object
    comment: None | str

@dataclass(kw_only=True)
class VarDecl(Decl):
    site: Site
    obj: None | ellipsis | object
    flags: dict[str, bool]
    def get_annotation_sites(self) -> tuple[Site, ...]: ...

@dataclass(kw_only=True)
class FuncDecl(Decl):
    params: tuple[Site, ...]
    ret: None | Site
    obj: None | object
    decorators: tuple[str, ...]
    flags: dict[str, bool]
    def get_annotation_sites(self) -> tuple[Site, ...]: ...

@dataclass(kw_only=True)
class ClassDecl(Decl):
    bases: tuple[Site, ...]
    td_fields: tuple[Site, ...]
    is_typeddict: bool
    td_total: None | bool
    members: tuple[Decl, ...]
    obj: None | object
    decorators: tuple[str, ...]
    flags: dict[str, bool]
    type_params: tuple[str, ...]
    def get_children(self) -> tuple[Decl, ...]: ...
    def get_annotation_sites(self) -> tuple[Site, ...]: ...

@dataclass(kw_only=True)
class AliasDecl(Decl):
    value: None | Site
    obj: None | object
    type_params: tuple[str, ...]
    alias_type: None | object
    def get_annotation_sites(self) -> tuple[Site, ...]: ...

@dataclass(kw_only=True)
class ModuleDecl(Decl):
    obj: module
    members: list[Decl]
    def get_children(self) -> tuple[Decl, ...]: ...
    def iter_all_decls(self) -> Iterator[Decl]: ...
    def get_all_decls(self) -> list[Decl]: ...
