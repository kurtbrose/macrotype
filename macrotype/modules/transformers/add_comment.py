from __future__ import annotations

import inspect
import io
import re
import tokenize
from types import ModuleType

from macrotype.modules.ir import (
    AliasDecl,
    ClassDecl,
    Decl,
    FuncDecl,
    ModuleDecl,
    VarDecl,
)


def _line_comment(line: str) -> str | None:
    try:
        for tok in tokenize.generate_tokens(io.StringIO(line).readline):
            if tok.type == tokenize.COMMENT:
                return tok.string[1:].strip()
    except tokenize.TokenError:
        return None
    return None


def _extract_name(line: str) -> str | None:
    stripped = line.lstrip()
    if stripped.startswith("def "):
        return stripped[4:].split("(", 1)[0].strip()
    if stripped.startswith("class "):
        return stripped[6:].split("(", 1)[0].split(":", 1)[0].strip()
    if stripped.startswith("type "):
        tail = stripped[5:]
        return re.split(r"[\s\[=]", tail, 1)[0]
    m = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\s*[:=]", stripped)
    if m:
        return m.group(1)
    return None


def _build_comment_map_from_lines(lines: list[str]) -> dict[str, str]:
    cmap: dict[str, str] = {}
    for line in lines:
        comment = _line_comment(line)
        if not comment:
            continue
        name = _extract_name(line)
        if name:
            cmap[name] = comment
    return cmap


def _build_comment_map(obj: ModuleType | type) -> dict[str, str]:
    try:
        lines, _ = inspect.getsourcelines(obj)
    except OSError:
        return {}
    return _build_comment_map_from_lines(lines)


def _attach(sym: Decl, obj: object | None, cmap: dict[str, str]) -> None:
    comment = cmap.get(sym.name)
    sym.comment = comment

    match sym:
        case VarDecl(site=site):
            site.comment = comment
        case AliasDecl(value=site):
            if site:
                site.comment = comment
        case FuncDecl():
            pass
        case ClassDecl(td_fields=fields, members=members):
            if inspect.isclass(obj):
                inner_map = _build_comment_map(obj)
                for f in fields:
                    f.comment = inner_map.get(f.name)
                for m in members:
                    m_obj = m.obj
                    _attach(m, m_obj, inner_map)


def add_comments(mi: ModuleDecl) -> None:
    """Attach same-line source comments to symbols within ``mi``."""
    cmap = _build_comment_map(mi.obj)
    for sym in mi.members:
        _attach(sym, sym.obj, cmap)
