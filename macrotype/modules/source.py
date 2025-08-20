from __future__ import annotations

"""Utilities for extracting source metadata."""

import ast
import io
import re
import tokenize
from collections import defaultdict
from typing import Dict, Set

from .ir import SourceInfo

# Comments matching this pattern are considered "pragma" headers that should be
# preserved in generated stubs.  Other leading comments are treated as regular
# source comments.
PRAGMA_PREFIX = re.compile(r"#\s*(?:type:|pyright:|mypy:|pyre-|pyre:)")


def _mentions_type_checking(expr: ast.AST) -> bool:
    if isinstance(expr, ast.Name) and expr.id == "TYPE_CHECKING":
        return True
    if (
        isinstance(expr, ast.Attribute)
        and isinstance(expr.value, ast.Name)
        and expr.value.id == "typing"
        and expr.attr == "TYPE_CHECKING"
    ):
        return True
    return any(_mentions_type_checking(c) for c in ast.iter_child_nodes(expr))


def _tc_imports_from_tree(tree: ast.AST, *, allow_complex: bool) -> Dict[str, Set[str]]:
    imports: Dict[str, Set[str]] = defaultdict(set)
    for node in ast.walk(tree):
        if not isinstance(node, ast.If) or not _mentions_type_checking(node.test):
            continue
        if node.orelse and not allow_complex:
            raise RuntimeError("Skipped module due to TYPE_CHECKING guard")
        for stmt in node.body:
            if (
                isinstance(stmt, ast.ImportFrom)
                and stmt.module
                and stmt.level == 0
                and not any(alias.asname for alias in stmt.names)
            ):
                for alias in stmt.names:
                    imports[stmt.module].add(alias.name)
            elif isinstance(stmt, ast.ImportFrom | ast.Import) and allow_complex:
                continue
            else:
                if allow_complex:
                    continue
                raise RuntimeError("Skipped module due to TYPE_CHECKING guard")
    return imports


def extract_type_checking_imports(
    code: str, *, allow_type_checking: bool = False
) -> Dict[str, Set[str]]:
    tree = ast.parse(code)
    return _tc_imports_from_tree(tree, allow_complex=allow_type_checking)


def extract_source_info(code: str, *, allow_type_checking: bool = False) -> SourceInfo:
    """Return SourceInfo for *code* including parsed AST."""

    comments: dict[int, str] = {}
    header: list[str] = []
    first_code = None
    tokens = tokenize.generate_tokens(io.StringIO(code).readline)
    for tok_type, tok_str, start, _, _ in tokens:
        if tok_type == tokenize.COMMENT:
            comments[start[0]] = tok_str
            if first_code is None:
                header.append(tok_str)
        elif first_code is None and tok_type not in (
            tokenize.COMMENT,
            tokenize.NL,
            tokenize.NEWLINE,
            tokenize.ENCODING,
        ):
            first_code = start[0]

    tree = ast.parse(code)
    line_map: dict[str, int] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            line_map[node.name] = node.lineno
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                line_map[node.target.id] = node.lineno
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    line_map[t.id] = node.lineno
        elif hasattr(ast, "TypeAlias") and isinstance(node, ast.TypeAlias):
            line_map[node.name] = node.lineno

    tc_imports = _tc_imports_from_tree(tree, allow_complex=allow_type_checking)

    info = SourceInfo(
        headers=header,
        comments=comments,
        line_map=line_map,
        tc_imports=tc_imports,
        code=code,
    )
    info._tree = tree
    return info


__all__ = ["extract_source_info", "extract_type_checking_imports", "PRAGMA_PREFIX"]
