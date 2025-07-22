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


def test_dataclass_decorators():
    src = Path(__file__).with_name("dataclass_sample.py")
    loaded = load_module_from_path(src)
    module = PyiModule.from_module(loaded)
    generated = module.render()

    expected_path = Path(__file__).with_name("dataclass_sample.pyi")
    expected = expected_path.read_text().splitlines()

    assert generated == expected


def test_nested_dataclass():
    src = Path(__file__).with_name("nested_dataclass.py")
    loaded = load_module_from_path(src)
    module = PyiModule.from_module(loaded)
    generated = module.render()

    expected_path = Path(__file__).with_name("nested_dataclass.pyi")
    expected = expected_path.read_text().splitlines()

    assert generated == expected


def test_variadic_typevar_tuple():
    src = Path(__file__).with_name("variadic.py")
    loaded = load_module_from_path(src)
    module = PyiModule.from_module(loaded)
    generated = module.render()

    expected_path = Path(__file__).with_name("variadic.pyi")
    expected = expected_path.read_text().splitlines()

    assert generated == expected


def test_new_style_generic_class():
    src = Path(__file__).with_name("new_generic.py")
    loaded = load_module_from_path(src)
    module = PyiModule.from_module(loaded)
    generated = module.render()

    expected_path = Path(__file__).with_name("new_generic.pyi")
    expected = expected_path.read_text().splitlines()

    assert generated == expected


def test_old_style_generic_class():
    src = Path(__file__).with_name("old_generic.py")
    loaded = load_module_from_path(src)
    module = PyiModule.from_module(loaded)
    generated = module.render()

    expected_path = Path(__file__).with_name("old_generic.pyi")
    expected = expected_path.read_text().splitlines()

    assert generated == expected
