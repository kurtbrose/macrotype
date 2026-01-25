# Generated via: macrotype macrotype
# Do not edit by hand
from __future__ import annotations
from collections import defaultdict
from macrotype.modules.emit import build_name_map, collect_all_annotations, flatten_annotation_atoms
from macrotype.modules.ir import ClassDecl, Decl, ImportBlock, ModuleDecl, TypeDefDecl

from typing import Iterable

_MODULE_ALIASES: dict[str, str]

def resolve_imports(mi: ModuleDecl) -> None: ...

def _collect_typing_names(symbols: Iterable[Decl]) -> set[str]: ...
