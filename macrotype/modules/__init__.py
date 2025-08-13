from __future__ import annotations

"""Module analysis pipeline."""

import typing as t
from types import ModuleType

from .emit import emit_module
from .scanner import ModuleInfo, scan_module


def from_module(glb_or_mod: ModuleType | t.Mapping[str, t.Any]) -> ModuleInfo:
    """Scan *glb_or_mod* into a ModuleInfo."""

    return scan_module(glb_or_mod)


__all__ = ["ModuleInfo", "from_module", "emit_module", "scan_module"]
