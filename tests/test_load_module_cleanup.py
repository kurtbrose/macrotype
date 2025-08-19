import sys
from pathlib import Path

from macrotype.stubgen import load_module


def test_load_module_prunes_sys_modules(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg" / "subpkg"
    pkg.mkdir(parents=True)
    (tmp_path / "pkg" / "__init__.py").write_text("")
    (pkg / "__init__.py").write_text("")
    (pkg / "other.py").write_text("VALUE = 1\n")
    (pkg / "mod.py").write_text("from .other import VALUE\n")

    sys.path.insert(0, str(tmp_path))
    try:
        before = set(sys.modules)
        mod = load_module("pkg.subpkg.mod")
        assert mod.VALUE == 1
        name = mod.__name__
        assert name in sys.modules
        assert mod.__package__ == "pkg.subpkg"
        cleanup = getattr(mod, "__cleanup__")
        cleanup()
        after = set(sys.modules)
        assert name not in sys.modules
        assert before == after
    finally:
        sys.path.remove(str(tmp_path))
