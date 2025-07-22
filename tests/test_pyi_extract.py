import sys
from pathlib import Path
import pytest

# Ensure the package root is on sys.path when running tests directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from macrotype.pyi_extract import PyiModule
from macrotype.stubgen import load_module_from_path


CASES = [
    ("annotations.py", "annotations.pyi"),
    pytest.param(
        "annotations_13.py",
        "annotations_13.pyi",
        marks=pytest.mark.skipif(sys.version_info < (3, 13), reason="requires Python 3.13+"),
    ),
]


@pytest.mark.parametrize("src, expected", CASES)
def test_stub_generation_matches_expected(src: str, expected: str) -> None:
    src_path = Path(__file__).with_name(src)
    loaded = load_module_from_path(src_path)
    module = PyiModule.from_module(loaded)
    generated = module.render()

    expected_path = Path(__file__).with_name(expected)
    expected_lines = expected_path.read_text().splitlines()

    assert generated == expected_lines
