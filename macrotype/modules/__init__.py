from __future__ import annotations

"""Module analysis pipeline."""

from types import ModuleType

from .add_comment_transform import add_comments
from .emit import emit_module
from .scanner import ModuleInfo, scan_module


def from_module(mod: ModuleType) -> ModuleInfo:
    """Scan *mod* into a ModuleInfo and attach comments."""

    mi = scan_module(mod)
    add_comments(mi)
    return mi


__all__ = ["ModuleInfo", "add_comments", "from_module", "emit_module", "scan_module"]
