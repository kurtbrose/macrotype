from pathlib import Path

from macrotype.stubgen import load_module_from_path


def test_load_module_reuses_existing_modules() -> None:
    base = Path(__file__).with_name("reuse_pkg")
    mod_b = load_module_from_path(base / "b.py")
    mod_a = load_module_from_path(base / "a.py")
    assert mod_a.User is mod_b.User
