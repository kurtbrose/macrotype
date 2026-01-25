# Generated via: macrotype macrotype
# Do not edit by hand
from __future__ import annotations
from dataclasses import dataclass, replace
from macrotype.types.ir import ParsedTy, ResolvedTy, Ty, TyAny, TyApp, TyCallable, TyForward, TyLiteral, TyNever, TyParamSpec, TyRoot, TyType, TyTypeVar, TyTypeVarTuple, TyUnion, TyUnpack

from typing import NewType

ParsedTy = NewType("ParsedTy", TyRoot)

ResolvedTy = NewType("ResolvedTy", TyRoot)

@dataclass(frozen=True)
class ResolveEnv:
    module: str
    imports: dict[str, type]

def resolve(t: ParsedTy | Ty, env: ResolveEnv) -> ResolvedTy: ...

def _res(node: None | Ty, env: ResolveEnv) -> None | Ty: ...
