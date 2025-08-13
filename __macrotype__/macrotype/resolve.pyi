# Generated via: macrotype macrotype
# Do not edit by hand
from dataclasses import dataclass
from macrotype.types.ir import Ty

@dataclass(frozen=True)
class ResolveEnv:
    module: str
    imports: dict[str, type]

def resolve(t: ParsedTy | Ty, env: ResolveEnv) -> ResolvedTy: ...

def _res(node: Ty, env: ResolveEnv) -> Ty: ...
