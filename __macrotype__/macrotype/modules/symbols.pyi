# Generated via: manual update to reflect code changes
from dataclasses import dataclass
from types import EllipsisType, ModuleType
from typing import Iterator, Literal, Optional

@dataclass(kw_only=True)
class Symbol:
    name: str
    comment: Optional[str]
    emit: bool

    def get_children(self) -> tuple[Symbol, ...]: ...
    def get_annotation_sites(self) -> tuple[Site, ...]: ...
    def walk(self) -> Iterator[Symbol]: ...

@dataclass(kw_only=True)
class Site:
    role: Literal["var", "return", "param", "base", "alias_value", "td_field"]
    name: Optional[str]
    index: Optional[int]
    annotation: object
    comment: Optional[str]

@dataclass(kw_only=True)
class VarSymbol(Symbol):
    site: Site
    initializer: object | EllipsisType
    flags: dict[str, bool]

    def get_annotation_sites(self) -> tuple[Site, ...]: ...

@dataclass(kw_only=True)
class FuncSymbol(Symbol):
    params: tuple[Site, ...]
    ret: Optional[Site]
    decorators: tuple[str, ...]
    flags: dict[str, bool]

    def get_annotation_sites(self) -> tuple[Site, ...]: ...

@dataclass(kw_only=True)
class ClassSymbol(Symbol):
    bases: tuple[Site, ...]
    td_fields: tuple[Site, ...]
    is_typeddict: bool
    td_total: Optional[bool]
    members: tuple[Symbol, ...]
    decorators: tuple[str, ...]
    flags: dict[str, bool]

    def get_children(self) -> tuple[Symbol, ...]: ...
    def get_annotation_sites(self) -> tuple[Site, ...]: ...

@dataclass(kw_only=True)
class TypeDefSymbol(Symbol):
    value: Optional[Site]
    type_params: tuple[str, ...]
    obj_type: object | None

    def get_annotation_sites(self) -> tuple[Site, ...]: ...

@dataclass
class ModuleInfo:
    mod: ModuleType
    symbols: list[Symbol]

    def iter_all_symbols(self) -> Iterator[Symbol]: ...
    def get_all_symbols(self) -> list[Symbol]: ...
