# Generated via: macrotype macrotype
# Do not edit by hand
from macrotype.modules.scanner import ModuleInfo
from macrotype.modules.symbols import Symbol
from macrotype.types.emit import EmitCtx

INDENT: str

def emit_module(mi: ModuleInfo) -> list[str]: ...

def _emit_symbol(sym: Symbol, ctx: EmitCtx, *, indent: int) -> list[str]: ...
