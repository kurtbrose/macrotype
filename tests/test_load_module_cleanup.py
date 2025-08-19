import sys
from pathlib import Path

from macrotype.stubgen import load_module


def test_load_module_leaves_sys_modules_alone(tmp_path: Path) -> None:
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
        # modules remain loaded and no cleanup hook is installed
        assert not hasattr(mod, "__cleanup__")
        assert "pkg.subpkg.other" in sys.modules
        after = set(sys.modules)
        assert before <= after
    finally:
        sys.path.remove(str(tmp_path))
        for name in ["pkg.subpkg.mod", "pkg.subpkg.other", "pkg.subpkg", "pkg"]:
            sys.modules.pop(name, None)
