from __future__ import annotations

"""Module analysis pipeline."""

from types import ModuleType

from .add_comment_transform import add_comments
from .alias_transform import synthesize_aliases
from .dataclass_transform import transform_dataclasses
from .descriptor_transform import normalize_descriptors
from .emit import emit_module
from .flag_transform import normalize_flags
from .foreign_symbol_transform import canonicalize_foreign_symbols
from .overload_transform import expand_overloads
from .scanner import ModuleInfo, scan_module
from .typeddict_transform import prune_inherited_typeddict_fields


def from_module(mod: ModuleType) -> ModuleInfo:
    """Scan *mod* into a ModuleInfo and attach comments."""

    mi = scan_module(mod)
    canonicalize_foreign_symbols(mi)
    synthesize_aliases(mi)
    transform_dataclasses(mi)
    prune_inherited_typeddict_fields(mi)
    normalize_descriptors(mi)
    normalize_flags(mi)
    expand_overloads(mi)
    add_comments(mi)
    return mi


__all__ = [
    "ModuleInfo",
    "add_comments",
    "from_module",
    "expand_overloads",
    "normalize_flags",
    "normalize_descriptors",
    "canonicalize_foreign_symbols",
    "synthesize_aliases",
    "prune_inherited_typeddict_fields",
    "emit_module",
    "scan_module",
    "transform_dataclasses",
]
