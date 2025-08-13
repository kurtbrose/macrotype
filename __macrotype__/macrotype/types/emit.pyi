# Generated via: macrotype macrotype/types/emit.py -o __macrotype__/macrotype/types/emit.pyi
# Do not edit by hand
from dataclasses import dataclass

from macrotype.types.ir import Ty, TyRoot

EllipsisType = ellipsis

@dataclass
class EmitCtx:
    typing_needed: set[str]
    prefer_from_typing: bool
    def need(self, *names: str) -> None: ...

def emit(t: Ty, ctx: EmitCtx | None) -> str: ...
def emit_top(t: TyRoot, ctx: EmitCtx | None) -> str: ...
def _emit(n: Ty, ctx: EmitCtx) -> str: ...
def _emit_no_annos(n: Ty, ctx: EmitCtx) -> str: ...
