# Generated via: macrotype macrotype
# Do not edit by hand
from __future__ import annotations
from dataclasses import replace
from macrotype.types.ir import Ty, TyAny, TyApp, TyCallable, TyForward, TyLiteral, TyNever, TyParamSpec, TyRoot, TyType, TyTypeVar, TyTypeVarTuple, TyUnion, TyUnpack

from typing import Any

def unparse(t: Ty) -> Any: ...

def unparse_top(root: TyRoot) -> Any: ...

def _apply_annos(inner: Any, tree) -> Any: ...

def _unparse(n: Ty) -> Any: ...

def _unparse_no_annos(n: Ty) -> Any: ...
