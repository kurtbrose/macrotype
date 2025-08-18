# Generated via: macrotype macrotype
# Do not edit by hand
from __future__ import annotations

from typing import Any

from macrotype.modules.ir import ClassDecl, FuncDecl, ModuleDecl

annotations = annotations

def _normalize_function(sym: FuncDecl, fn: Any, is_method: bool) -> None: ...
def _normalize_class(sym: ClassDecl, cls: type) -> None: ...
def normalize_flags(mi: ModuleDecl) -> None: ...
