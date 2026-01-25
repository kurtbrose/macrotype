# Generated via: macrotype macrotype
# Do not edit by hand
from dataclasses import replace
from macrotype.meta_types import get_overloads
from macrotype.modules.ir import ClassDecl, Decl, FuncDecl, ModuleDecl

from typing import Any, Callable

_get_overloads = get_overloads

def _annotation_for_value(value: Any) -> Any: ...

def _make_literal_overload(fn: Callable, args: tuple, kwargs: dict, result: Any) -> Callable: ...

def _expand_function(fn: Callable, sym: FuncDecl, enclosing: tuple[str, ...]) -> list[FuncDecl]: ...

def _get_function(sym: FuncDecl) -> Callable | None: ...

def _transform_class(sym: ClassDecl) -> None: ...

def expand_overloads(mi: ModuleDecl) -> None: ...
