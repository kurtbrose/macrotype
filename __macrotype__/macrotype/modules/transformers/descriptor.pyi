# Generated via: macrotype macrotype
# Do not edit by hand
from __future__ import annotations

from functools import partialmethod
from typing import Any

from macrotype.modules.ir import ClassDecl, FuncDecl, ModuleDecl

annotations = annotations

_ATTR_DECORATORS: dict[type, tuple[str, str]]

def _unwrap_descriptor(obj: Any) -> Any | None: ...
def _extract_partialmethod(pm: partialmethod, cls: type, name: str) -> Any: ...
def _descriptor_members(attr_name: str, attr: Any, cls: type) -> list[FuncDecl]: ...
def _transform_class(sym: ClassDecl, cls: type) -> None: ...
def normalize_descriptors(mi: ModuleDecl) -> None: ...
