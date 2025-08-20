from __future__ import annotations

import ast
import typing as t
from pathlib import Path

from macrotype.modules.ir import FuncDecl, ModuleDecl, VarDecl
from macrotype.modules.scanner import _eval_annotation


def _has_custom_class_getitem(obj: object) -> bool:
    return (
        isinstance(obj, type)
        and "__class_getitem__" in obj.__dict__
        and obj.__module__ not in {"builtins", "typing"}
    )


def _needs_recover(obj: object) -> bool:
    return _has_custom_class_getitem(obj) and t.get_origin(obj) is None


def _build_maps(tree: ast.Module, code: str):
    var_map: dict[str, str] = {}
    param_map: dict[tuple[str, str], str] = {}
    ret_map: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            var_map[node.target.id] = ast.get_source_segment(code, node.annotation) or ""
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fname = node.name
            if node.returns is not None:
                ret_map[fname] = ast.get_source_segment(code, node.returns) or ""
            args = list(node.args.posonlyargs) + list(node.args.args) + list(node.args.kwonlyargs)
            for arg in args:
                if arg.annotation is not None:
                    param_map[(fname, arg.arg)] = ast.get_source_segment(code, arg.annotation) or ""
            if node.args.vararg and node.args.vararg.annotation is not None:
                param_map[(fname, node.args.vararg.arg)] = (
                    ast.get_source_segment(code, node.args.vararg.annotation) or ""
                )
            if node.args.kwarg and node.args.kwarg.annotation is not None:
                param_map[(fname, node.args.kwarg.arg)] = (
                    ast.get_source_segment(code, node.args.kwarg.annotation) or ""
                )
    return var_map, param_map, ret_map


def _apply_recover(site, expr: str | None, name: str, glb: dict[str, t.Any]) -> None:
    if not expr or "[" not in expr:
        return
    new_ann = _eval_annotation(expr, glb)
    if isinstance(new_ann, str):
        raise RuntimeError(
            f"Annotation for {name} uses non-standard __class_getitem__; switch to a string annotation"
        )
    site.annotation = new_ann


def recover_custom_generics(mi: ModuleDecl) -> None:
    if mi.source is None:
        return
    file = getattr(mi.obj, "__file__", None)
    if not file:
        return
    code = Path(file).read_text()
    tree = ast.parse(code)
    var_map, param_map, ret_map = _build_maps(tree, code)
    glb = vars(mi.obj)
    for decl in mi.members:
        if isinstance(decl, VarDecl):
            site = decl.site
            if _needs_recover(site.annotation):
                expr = var_map.get(decl.name)
                _apply_recover(site, expr, decl.name, glb)
        elif isinstance(decl, FuncDecl):
            for site in decl.get_annotation_sites():
                if not _needs_recover(site.annotation):
                    continue
                if site.role == "return":
                    expr = ret_map.get(decl.name)
                    _apply_recover(site, expr, f"{decl.name} return", glb)
                elif site.role == "param" and site.name is not None:
                    expr = param_map.get((decl.name, site.name))
                    _apply_recover(site, expr, f"{decl.name}.{site.name}", glb)


__all__ = ["recover_custom_generics"]
