# Generated via: macrotype macrotype/resolve.py -o __macrotype__/macrotype/resolve.pyi
# Do not edit by hand
from dataclasses import dataclass
from macrotype.types_ir import Ty

@dataclass(frozen=True)
class ResolveEnv:
    module: str
    imports: dict[str, str]

def resolve(t: ParsedTy, env: ResolveEnv) -> ResolvedTy: ...

def _res(node: Ty, env: ResolveEnv) -> Ty: ...
