# Generated via: macrotype macrotype/modules/__init__.py -o __macrotype__/macrotype/modules/__init__/__init__.pyi
# Do not edit by hand
from collections.abc import Mapping
from typing import Any

from macrotype.modules.scanner import ModuleInfo

ModuleType = module

def from_module(glb_or_mod: Mapping[str, Any] | module) -> ModuleInfo: ...
def _apply_types(mi: ModuleInfo) -> ModuleInfo: ...
