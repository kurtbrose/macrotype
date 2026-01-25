# Generated via: macrotype macrotype
# Do not edit by hand
from __future__ import annotations
from macrotype.modules.ir import ClassDecl, FuncDecl, ModuleDecl, Site
from macrotype.types.ir import TyApp, TyCallable, TyParamSpec, TyTypeVar, TyTypeVarTuple, TyUnion, TyUnpack
from macrotype.types.parse import parse_root

from typing import Any, Callable

def _format_type_param(param: Any) -> str: ...

def _find_typevars(obj: Any) -> set[str]: ...

def _transform_class(sym: ClassDecl, cls: type) -> None: ...

def _transform_function(sym: FuncDecl, fn: Callable, enclosing: tuple[str, ...]) -> None: ...

def transform_generics(mi: ModuleDecl) -> None: ...
