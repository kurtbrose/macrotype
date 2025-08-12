# Generated via: macrotype macrotype
# Do not edit by hand
from dataclasses import dataclass
from macrotype.types.ir import Ty

@dataclass
class EmitCtx:
    typing_needed: set[str]
    prefer_from_typing: bool
    def need(self, *names: str) -> None: ...

def emit(t: ValidatedTy, ctx: EmitCtx | None) -> str: ...

def _emit(n: Ty, ctx: EmitCtx) -> str: ...

def _emit_no_annos(n: Ty, ctx: EmitCtx) -> str: ...
