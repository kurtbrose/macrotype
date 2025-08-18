# Generated via: macrotype macrotype
# Do not edit by hand
from __future__ import annotations

from dataclasses import dataclass
from typing import NewType

from macrotype.types.ir import ParsedTy, ResolvedTy, Ty, TyRoot

annotations = annotations

ParsedTy = NewType("ParsedTy", TyRoot)

ResolvedTy = NewType("ResolvedTy", TyRoot)

@dataclass(frozen=True)
class ResolveEnv:
    module: str
    imports: dict[str, type]

def resolve(t: ParsedTy | Ty, env: ResolveEnv) -> ResolvedTy: ...
def _res(node: None | Ty, env: ResolveEnv) -> None | Ty: ...
