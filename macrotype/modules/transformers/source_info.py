from __future__ import annotations

"""Attach source metadata to a ModuleDecl."""

from macrotype.modules.ir import ModuleDecl, SourceInfo


def add_source_info(mi: ModuleDecl, source_info: SourceInfo | None = None) -> None:
    """Populate ``mi.source`` with provided source metadata."""
    mi.source = source_info or SourceInfo(headers=[], comments={}, line_map={})
    if source_info is not None:
        for mod, names in source_info.tc_imports.items():
            mi.imports.froms.setdefault(mod, set()).update(names)


__all__ = ["add_source_info"]
