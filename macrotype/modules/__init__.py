from __future__ import annotations

"""Module analysis pipeline."""

from types import ModuleType

from .add_comment_transform import add_comments
from .alias_transform import synthesize_aliases
from .dataclass_transform import transform_dataclasses
from .descriptor_transform import normalize_descriptors
from .emit import emit_module
from .overload_transform import expand_overloads
from .scanner import ModuleInfo, scan_module


def from_module(mod: ModuleType) -> ModuleInfo:
    """Scan *mod* into a ModuleInfo and attach comments."""

    mi = scan_module(mod)
    synthesize_aliases(mi)
    transform_dataclasses(mi)
    normalize_descriptors(mi)
    expand_overloads(mi)
    add_comments(mi)
    return mi


__all__ = [
    "ModuleInfo",
    "add_comments",
    "from_module",
    "expand_overloads",
    "normalize_descriptors",
    "synthesize_aliases",
    "emit_module",
    "scan_module",
    "transform_dataclasses",
]
