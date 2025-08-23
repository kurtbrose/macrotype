from __future__ import annotations

import ast
import typing as t

from macrotype.modules.ir import AnnExpr, FuncDecl, ModuleDecl, VarDecl
from macrotype.modules.scanner import eval_annotation


def _has_custom_class_getitem(obj: object) -> bool:
    if not isinstance(obj, type):
        return False
    for cls in obj.__mro__:
        if "__class_getitem__" in cls.__dict__ and cls.__module__ not in {"builtins", "typing"}:
            return True
    return False


def _needs_recover(obj: object) -> bool:
    if _has_custom_class_getitem(obj) and t.get_origin(obj) is None:
        return True
    origin = t.get_origin(obj)
    if origin is None:
        return False
    return any(_needs_recover(arg) for arg in t.get_args(obj))


def _build_maps(tree: ast.Module, code: str):
    var_map: dict[str, str] = {}
    param_map: dict[tuple[str, int, str], str] = {}
    ret_map: dict[tuple[str, int], str] = {}
    counts: dict[str, int] = {}
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            var_map[node.target.id] = ast.get_source_segment(code, node.annotation) or ""
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fname = node.name
            idx = counts.get(fname, 0)
            counts[fname] = idx + 1
            if node.returns is not None:
                ret_map[(fname, idx)] = ast.get_source_segment(code, node.returns) or ""
            args = list(node.args.posonlyargs) + list(node.args.args) + list(node.args.kwonlyargs)
            for arg in args:
                if arg.annotation is not None:
                    param_map[(fname, idx, arg.arg)] = (
                        ast.get_source_segment(code, arg.annotation) or ""
                    )
            if node.args.vararg and node.args.vararg.annotation is not None:
                param_map[(fname, idx, node.args.vararg.arg)] = (
                    ast.get_source_segment(code, node.args.vararg.annotation) or ""
                )
            if node.args.kwarg and node.args.kwarg.annotation is not None:
                param_map[(fname, idx, node.args.kwarg.arg)] = (
                    ast.get_source_segment(code, node.args.kwarg.annotation) or ""
                )
    return var_map, param_map, ret_map


def _apply_recover(
    site,
    expr: str | None,
    name: str,
    glb: dict[str, t.Any],
    lcl: dict[str, t.Any] | None = None,
) -> None:
    if not expr or "[" not in expr:
        return
    new_ann = eval_annotation(expr, glb, lcl)
    if isinstance(new_ann, str):
        raise RuntimeError(
            f"Annotation for {name} uses non-standard __class_getitem__; switch to a string annotation"
        )
    if _needs_recover(new_ann):
        site.annotation = AnnExpr(expr=expr, evaluated=new_ann)
    else:
        site.annotation = new_ann


def recover_custom_generics(mi: ModuleDecl) -> None:
    if mi.source is None or mi.source.code is None:
        return
    code = mi.source.code
    tree = mi.source.tree
    var_map, param_map, ret_map = _build_maps(tree, code)
    glb = vars(mi.obj)
    fn_counts: dict[str, int] = {}
    for decl in mi.iter_all_decls():
        if isinstance(decl, VarDecl):
            site = decl.site
            if _needs_recover(site.annotation):
                expr = var_map.get(decl.name)
                _apply_recover(site, expr, decl.name, glb)
        elif isinstance(decl, FuncDecl):
            idx = fn_counts.get(decl.name, 0)
            fn_counts[decl.name] = idx + 1
            lcl = {tp.__name__: tp for tp in getattr(decl.obj, "__type_params__", ())}
            for site in decl.get_annotation_sites():
                if not _needs_recover(site.annotation):
                    continue
                if site.role == "return":
                    expr = ret_map.get((decl.name, idx))
                    _apply_recover(site, expr, f"{decl.name} return", glb, lcl)
                elif site.role == "param" and site.name is not None:
                    expr = param_map.get((decl.name, idx, site.name))
                    _apply_recover(site, expr, f"{decl.name}.{site.name}", glb, lcl)


__all__ = ["recover_custom_generics"]
