# Generated via: macrotype macrotype/modules/source.py -o __macrotype__/macrotype/modules/source.pyi
# Do not edit by hand
from __future__ import annotations
from ast import AST
from collections import defaultdict
from re import Pattern

PRAGMA_PREFIX = Pattern

def _mentions_type_checking(expr: AST) -> bool: ...

def _tc_imports_from_tree(tree: AST, allow_complex: bool) -> dict[str, set[str]]: ...

def extract_type_checking_imports(code: str, allow_type_checking: bool) -> dict[str, set[str]]: ...

def extract_source_info(code: str, allow_type_checking: bool) -> tuple[list[str], dict[int, str], dict[str, int], dict[str, set[str]]]: ...
