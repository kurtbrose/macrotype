from __future__ import annotations

import inspect

from macrotype.modules.ir import ModuleDecl, VarDecl


def infer_constant_types(mi: ModuleDecl) -> None:
    """Populate missing annotations for simple constant assignments."""
    for decl in mi.get_all_decls():
        if not isinstance(decl, VarDecl):
            continue
        site = decl.site
        if site.annotation is not inspect._empty:
            continue
        obj = decl.obj
        if obj is None:
            continue
        ty = type(obj)
        if ty in {bool, int, float, str}:
            site.annotation = ty
