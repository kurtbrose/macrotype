import sys
from pathlib import Path

# Ensure the package root is on sys.path when running tests directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from macrotype.pyi_extract import PyiModule
import tests.all_annotations as all_annotations


def test_stub_generation_matches_expected():
    module = PyiModule.from_module(all_annotations)
    generated = module.render()

    expected_path = Path(__file__).with_name("all_annotations.pyi")
    expected = expected_path.read_text().splitlines()

    assert generated == expected
