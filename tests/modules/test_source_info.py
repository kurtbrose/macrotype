from __future__ import annotations

import sys
from pathlib import Path

from macrotype.modules import from_module
from macrotype.modules.ir import SourceInfo
from macrotype.modules.source import extract_source_info
from macrotype.stubgen import load_module


def test_source_info_attached(tmp_path: Path) -> None:
    code = """# header1\n# header2\nX = 1\n"""
    path = tmp_path / "mod.py"
    path.write_text(code)
    sys.path.insert(0, str(tmp_path))
    try:
        mod = load_module("mod")
    finally:
        sys.path.remove(str(tmp_path))
    header, comments, line_map = extract_source_info(code)
    info = SourceInfo(headers=header, comments=comments, line_map=line_map)
    mi = from_module(mod, source_info=info)
    assert mi.source is not None
    assert mi.source.headers == ["# header1", "# header2"]
    assert mi.source.comments[1] == "# header1"
    assert mi.source.line_map["X"] == 3
    getattr(mod, "__cleanup__")()
