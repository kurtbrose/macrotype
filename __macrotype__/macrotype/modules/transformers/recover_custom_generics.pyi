# Generated via: macrotype macrotype
# Do not edit by hand
from __future__ import annotations
from ast import Module
from macrotype.modules.ir import AnnExpr, FuncDecl, ModuleDecl, VarDecl
from macrotype.modules.scanner import eval_annotation

from typing import Any

def _has_custom_class_getitem(obj: object) -> bool: ...

def _needs_recover(obj: object) -> bool: ...

def _build_maps(tree: Module, code: str): ...

def _apply_recover(site, expr: None | str, name: str, glb: dict[str, Any], lcl: None | dict[str, Any]) -> None: ...

def recover_custom_generics(mi: ModuleDecl) -> None: ...
