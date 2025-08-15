from pathlib import Path

import pytest

from macrotype.stubgen import load_module_from_path, stub_lines
from macrotype.types_ast import InvalidTypeError


def test_invalid_literal_error():
    path = Path(__file__).with_name("annotations_invalid.py")
    mod = load_module_from_path(path)
    with pytest.raises(InvalidTypeError) as exc:
        stub_lines(mod)
    msg = str(exc.value)
    assert "Invalid Literal value" in msg
    assert f"{path}:4" in msg
    assert "Literal values must" in msg


def test_invalid_non_type_error():
    path = Path(__file__).with_name("annotations_invalid_non_type.py")
    mod = load_module_from_path(path)
    with pytest.raises(InvalidTypeError) as exc:
        stub_lines(mod)
    msg = str(exc.value)
    assert "Unrecognized type annotation" in msg
    assert f"{path}:2" in msg
    assert "valid type or typing construct" in msg


def test_unresolved_string_raises_error(tmp_path):
    code = 'X: "Missing"\n'
    path = tmp_path / "mod.py"
    path.write_text(code)
    mod = load_module_from_path(path)
    with pytest.raises(InvalidTypeError) as exc:
        stub_lines(mod)
    msg = str(exc.value)
    assert "Unresolved forward reference" in msg
    assert f"{path}:1" in msg


def test_forward_ref_raises_error(tmp_path):
    code = 'import typing\nX: typing.ForwardRef("Missing")\n'
    path = tmp_path / "mod.py"
    path.write_text(code)
    mod = load_module_from_path(path)
    with pytest.raises(InvalidTypeError) as exc:
        stub_lines(mod)
    msg = str(exc.value)
    assert "Unresolved forward reference" in msg
    assert f"{path}:2" in msg


def test_misplaced_ellipsis_in_tuple_raises_error() -> None:
    path = Path(__file__).with_name("strict_error.py")
    mod = load_module_from_path(path)
    with pytest.raises(InvalidTypeError) as exc:
        stub_lines(mod)
    msg = str(exc.value)
    assert "Ellipsis" in msg
    assert f"{path}:4" in msg
    assert "final position" in msg
