from __future__ import annotations

"""Attach source metadata to a ModuleDecl."""

from macrotype.modules.ir import ModuleDecl, SourceInfo


def add_source_info(mi: ModuleDecl) -> None:
    """Populate ``mi.source`` with source metadata from its module."""
    mod = mi.obj
    mi.source = SourceInfo(
        headers=getattr(mod, "__macrotype_header_pragmas__", []),
        comments=getattr(mod, "__macrotype_comments__", {}),
        line_map=getattr(mod, "__macrotype_line_map__", {}),
    )


__all__ = ["add_source_info"]
