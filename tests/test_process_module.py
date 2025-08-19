import sys
from pathlib import Path

from macrotype.stubgen import load_module, process_module


def test_process_module_defaults_to_module_file(tmp_path: Path) -> None:
    pkg = tmp_path / "process_pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("VALUE = 1\n")

    sys.path.insert(0, str(tmp_path))
    try:
        mod = load_module("process_pkg")
        out = process_module(mod)
        assert out == pkg / "__init__.pyi"
        assert "VALUE: int" in out.read_text()
    finally:
        sys.path.remove(str(tmp_path))
        sys.modules.pop("process_pkg", None)
