# Generated via: macrotype macrotype
# Do not edit by hand
from __future__ import annotations

from enum import EnumType

from macrotype.modules.ir import ClassDecl, ModuleDecl, TypeDefDecl

annotations = annotations

def _enum_members(klass: EnumType) -> list[TypeDefDecl]: ...
def _auto_enum_methods(klass: type) -> set[str]: ...
def _transform_class(sym: ClassDecl, cls: type) -> None: ...
def transform_enums(mi: ModuleDecl) -> None: ...
