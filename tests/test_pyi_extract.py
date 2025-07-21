import sys
from pathlib import Path

# Ensure the package root is on sys.path when running tests directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from macrotype.pyi_extract import PyiModule
from macrotype.stubgen import load_module_from_path


def test_stub_generation_matches_expected():
    src = Path(__file__).with_name("all_annotations.py")
    loaded = load_module_from_path(src)
    module = PyiModule.from_module(loaded)
    generated = module.render()

    expected_path = Path(__file__).with_name("all_annotations.pyi")
    expected = expected_path.read_text().splitlines()

    assert generated == expected
