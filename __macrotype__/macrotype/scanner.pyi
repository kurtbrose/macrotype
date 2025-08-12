# Generated via: macrotype macrotype/scanner.py -o __macrotype__/macrotype/scanner.pyi
# Do not edit by hand
from collections.abc import Mapping
from dataclasses import dataclass
from macrotype.types_ir import ClassSymbol, FuncSymbol, Provenance, Symbol
from typing import Any, Callable

ModuleType = module

@dataclass
class ModuleInfo:
    mod: module
    symbols: list[Symbol]
    provenance: str

def _is_dunder(name: str) -> bool: ...

def _source_prov(obj: Any, *, modname: str, key: str, name: str) -> Provenance: ...

def _mk_key(parent_key: None | str, modname: str, name: str) -> str: ...

def _get_modname(glb_or_mod: Mapping[str, Any] | module) -> str: ...

def _get_globals(glb_or_mod: Mapping[str, Any] | module) -> dict[str, Any]: ...

def scan_module(glb_or_mod: Mapping[str, Any] | module) -> ModuleInfo: ...

def _scan_function(fn: Callable[..., Any], *, modname: str, parent_key: None | str) -> FuncSymbol: ...

def _scan_class(cls: type, *, modname: str, parent_key: None | str) -> ClassSymbol: ...
