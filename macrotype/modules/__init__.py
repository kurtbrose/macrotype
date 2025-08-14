from __future__ import annotations

"""Module analysis pipeline."""

from types import ModuleType

from .emit import emit_module
from .scanner import ModuleInfo, scan_module

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
    "prune_protocol_methods",
    "emit_module",
    "scan_module",
    "transform_dataclasses",
]


def __getattr__(name: str):
    if name in {
        "add_comments",
        "canonicalize_foreign_symbols",
        "expand_overloads",
        "normalize_descriptors",
        "normalize_flags",
        "prune_inherited_typeddict_fields",
        "prune_protocol_methods",
        "synthesize_aliases",
        "transform_dataclasses",
    }:
        from . import transformers as _t

        return getattr(_t, name)
    raise AttributeError(name)


def from_module(mod: ModuleType) -> ModuleInfo:
    """Scan *mod* into a ModuleInfo and attach comments."""

    from . import transformers as _t

    mi = scan_module(mod)
    _t.canonicalize_foreign_symbols(mi)
    _t.synthesize_aliases(mi)
    _t.transform_dataclasses(mi)
    _t.prune_inherited_typeddict_fields(mi)
    _t.normalize_descriptors(mi)
    _t.normalize_flags(mi)
    _t.prune_protocol_methods(mi)
    _t.expand_overloads(mi)
    _t.add_comments(mi)
    return mi
