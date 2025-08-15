from __future__ import annotations

"""Utilities for extracting source metadata."""

import ast
import io
import tokenize


def extract_source_info(code: str) -> tuple[list[str], dict[int, str], dict[str, int]]:
    """Return header comments, comment map, and name line map for *code*."""

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

    return header, comments, line_map


__all__ = ["extract_source_info"]
