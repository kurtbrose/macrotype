"""Symbol dataclasses for scanning and IR.

This module re-exports the symbol-related dataclasses from ``types_ir``
so that other modules can import them without pulling in the entire
``types_ir`` module.
"""

from .types_ir import (
    AliasSymbol,
    ClassSymbol,
    FuncSymbol,
    Site,
    Symbol,
    VarSymbol,
)

__all__ = [
    "Symbol",
    "VarSymbol",
    "FuncSymbol",
    "ClassSymbol",
    "AliasSymbol",
    "Site",
]
