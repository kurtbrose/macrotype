# Generated via: manual update
from macrotype.modules.symbols import ClassSymbol, FuncSymbol, ModuleInfo, Symbol
from typing import Any, Callable

ModuleType = module

def _is_dunder(name: str) -> bool: ...

def scan_module(mod: module) -> ModuleInfo: ...

def _scan_function(fn: Callable[..., Any]) -> FuncSymbol: ...

def _scan_class(cls: type) -> ClassSymbol: ...

