# Generated via: macrotype macrotype -o /tmp/tmp.H5RxRdggo7
# Do not edit by hand
from macrotype.emit_type import EmitCtx
from macrotype.scanner import ModuleInfo
from macrotype.types_ir import Symbol

INDENT: str

def emit_module(mi: ModuleInfo) -> list[str]: ...

def _emit_symbol(sym: Symbol, ctx: EmitCtx, *, indent: int) -> list[str]: ...
