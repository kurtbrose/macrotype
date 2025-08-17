import importlib
import sys


def test_load_module_from_path_importlib_util(tmp_path):
    sys.modules.pop("importlib.util", None)
    if hasattr(importlib, "util"):
        delattr(importlib, "util")
    sys.modules.pop("macrotype.stubgen", None)

    import macrotype.stubgen as stubgen

    p = tmp_path / "m.py"
    p.write_text("x = 1\n")
    mod = stubgen.load_module_from_path(p)
    assert mod.x == 1
