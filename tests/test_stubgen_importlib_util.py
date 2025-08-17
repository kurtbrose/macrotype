import importlib
import sys


def test_load_module_from_path_without_importlib_util(tmp_path):
    sys.modules.pop("importlib.util", None)
    if hasattr(importlib, "util"):
        delattr(importlib, "util")
    import macrotype.stubgen as stubgen

    importlib.reload(stubgen)
    p = tmp_path / "m.py"
    p.write_text("x: int = 1\n")
    mod = stubgen.load_module_from_path(p)
    assert mod.x == 1
