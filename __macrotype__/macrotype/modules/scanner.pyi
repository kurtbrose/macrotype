# Generated via: macrotype macrotype
# Do not edit by hand
from dataclasses import dataclass
from macrotype.modules.symbols import ClassSymbol, FuncSymbol, Symbol
from typing import Any, Callable

ModuleType = module

@dataclass
class ModuleInfo:
    mod: module
    symbols: list[Symbol]

def _is_dunder(name: str) -> bool: ...

def scan_module(mod: module) -> ModuleInfo: ...

def _scan_function(fn: Callable[..., Any]) -> FuncSymbol: ...

def _scan_class(cls: type) -> ClassSymbol: ...
