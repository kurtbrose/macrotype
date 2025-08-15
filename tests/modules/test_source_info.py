from __future__ import annotations

from pathlib import Path

from macrotype.modules import from_module
from macrotype.stubgen import load_module_from_path


def test_source_info_attached(tmp_path: Path) -> None:
    code = """# header1\n# header2\nX = 1\n"""
    path = tmp_path / "mod.py"
    path.write_text(code)
    mod = load_module_from_path(path, module_name="test_source_info_mod")
    mi = from_module(mod)
    assert mi.source is not None
    assert mi.source.headers == ["# header1", "# header2"]
    assert mi.source.comments[1] == "# header1"
    assert mi.source.line_map["X"] == 3
