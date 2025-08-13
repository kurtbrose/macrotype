from types import ModuleType
from typing import Any, Mapping

from .emit_module import emit_module
from .scanner import ModuleInfo, scan_module
from .validate import ModuleValidationError, validate

def from_module(glb_or_mod: ModuleType | Mapping[str, Any]) -> ModuleInfo: ...

__all__ = [
    "ModuleInfo",
    "from_module",
    "emit_module",
    "scan_module",
    "validate",
    "ModuleValidationError",
]
