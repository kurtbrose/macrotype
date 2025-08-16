# Generated via: macrotype macrotype/modules/transformers/generic.py -o __macrotype__/macrotype/modules/transformers/generic.pyi
# Do not edit by hand
from __future__ import annotations

from typing import Any, Callable

from macrotype.modules.ir import ClassDecl, FuncDecl, ModuleDecl

annotations = annotations

def _format_type_param(param: Any) -> str: ...
def _transform_class(sym: ClassDecl, cls: type) -> None: ...
def _transform_function(sym: FuncDecl, fn: Callable, enclosing: tuple[str, ...]) -> None: ...
def transform_generics(mi: ModuleDecl) -> None: ...
