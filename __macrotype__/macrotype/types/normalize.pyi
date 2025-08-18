# Generated via: macrotype macrotype
# Do not edit by hand
from __future__ import annotations

from dataclasses import dataclass
from typing import NewType

from macrotype.types.ir import NormalizedTy, ResolvedTy, Ty, TyRoot

annotations = annotations

NormalizedTy = NewType("NormalizedTy", TyRoot)

ResolvedTy = NewType("ResolvedTy", TyRoot)

@dataclass(frozen=True)
class NormOpts:
    drop_annotated_any: bool
    typing_to_builtins: bool
    sort_unions: bool
    dedup_unions: bool

def norm(t: ResolvedTy | Ty, opts: None | NormOpts) -> NormalizedTy: ...
def _norm(n: None | Ty, o: NormOpts) -> None | Ty: ...
def _key(n: Ty) -> str: ...
