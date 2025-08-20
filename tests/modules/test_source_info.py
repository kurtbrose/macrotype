from __future__ import annotations

import sys
from pathlib import Path

from macrotype.modules import from_module
from macrotype.modules.source import extract_source_info
from macrotype.stubgen import load_module


def test_source_info_attached(tmp_path: Path) -> None:
    code = """# header1\n# header2\nX = 1\n"""
    path = tmp_path / "source_info_mod.py"
    path.write_text(code)
    sys.path.insert(0, str(tmp_path))
    try:
        mod = load_module("source_info_mod")
    finally:
        sys.path.remove(str(tmp_path))
        sys.modules.pop("source_info_mod", None)
    info = extract_source_info(code)
    mi = from_module(mod, source_info=info)
    assert mi.source is not None
    assert mi.source.headers == ["# header1", "# header2"]
    assert mi.source.comments[1] == "# header1"
    assert mi.source.line_map["X"] == 3


def test_source_info_tree_cached() -> None:
    code = "X = 1\n"
    info = extract_source_info(code)
    first = info.tree
    second = info.tree
    assert first is second
