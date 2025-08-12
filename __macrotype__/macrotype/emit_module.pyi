# Generated via: macrotype macrotype
# Do not edit by hand
from macrotype.scanner import ModuleInfo
from macrotype.types.emit import EmitCtx
from macrotype.types.symbols import Symbol

INDENT: str

def emit_module(mi: ModuleInfo) -> list[str]: ...

def _emit_symbol(sym: Symbol, ctx: EmitCtx, *, indent: int) -> list[str]: ...
