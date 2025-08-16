from __future__ import annotations

import inspect
import typing as t

from macrotype.modules.ir import ModuleDecl, VarDecl


def infer_constant_types(mi: ModuleDecl) -> None:
    """Populate annotations for simple constant assignments."""
    for decl in mi.get_all_decls():
        if not isinstance(decl, VarDecl):
            continue
        site = decl.site
        ann = site.annotation
        obj = decl.obj
        if obj is None:
            continue
        ty = type(obj)
        if ann is inspect._empty:
            if ty in {bool, int, float, str}:
                site.annotation = ty
            continue
        if ann is t.Final and ty in {bool, int, float, str}:
            site.annotation = t.Final[ty]
