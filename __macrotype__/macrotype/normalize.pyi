# Generated via: macrotype macrotype/normalize.py -o __macrotype__/macrotype/normalize.pyi
# Do not edit by hand
from dataclasses import dataclass
from macrotype.types_ir import Ty

@dataclass(frozen=True)
class NormOpts:
    drop_annotated_any: bool
    typing_to_builtins: bool
    sort_unions: bool
    dedup_unions: bool

def norm(t: ResolvedTy, opts: None | NormOpts) -> NormalizedTy: ...

def _norm(n: Ty, o: NormOpts) -> Ty: ...

def _key(n: Ty) -> str: ...
