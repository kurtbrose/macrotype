from __future__ import annotations

"""Attach source metadata to a ModuleDecl."""

from macrotype.modules.ir import ModuleDecl, SourceInfo


def add_source_info(mi: ModuleDecl, source_info: SourceInfo | None = None) -> None:
    """Populate ``mi.source`` with provided source metadata."""
    mi.source = source_info or SourceInfo(headers=[], comments={}, line_map={})


__all__ = ["add_source_info"]
