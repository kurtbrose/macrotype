from pathlib import Path

import pytest

from macrotype.stubgen import load_module_from_path, stub_lines
from macrotype.types.validate import TypeValidationError


def test_invalid_literal_error():
    path = Path(__file__).with_name("annotations_invalid.py")
    mod = load_module_from_path(path)
    with pytest.raises(TypeValidationError) as exc:
        stub_lines(mod, strict=True)
    msg = str(exc.value)
    assert "Illegal Literal value" in msg
    assert "Literal" in msg


def test_invalid_non_type_error():
    path = Path(__file__).with_name("annotations_invalid_non_type.py")
    mod = load_module_from_path(path)
    lines = stub_lines(mod, strict=True)
    assert lines[-1] == "BAD_NON_TYPE: 123"


def test_unresolved_string_kept_as_name(tmp_path):
    code = 'X: "Missing"\n'
    path = tmp_path / "mod.py"
    path.write_text(code)
    mod = load_module_from_path(path)
    lines = stub_lines(mod, strict=True)
    assert lines == ["X: Missing"]


def test_forward_ref_kept_as_name(tmp_path):
    code = 'import typing\nX: typing.ForwardRef("Missing")\n'
    path = tmp_path / "mod.py"
    path.write_text(code)
    mod = load_module_from_path(path)
    lines = stub_lines(mod, strict=True)
    assert lines[0] == "from typing import Missing"
    assert lines[-1] == "X: Missing"


def test_misplaced_ellipsis_in_tuple_raises_error() -> None:
    path = Path(__file__).with_name("strict_error.py")
    mod = load_module_from_path(path)
    with pytest.raises(TypeValidationError) as exc:
        stub_lines(mod, strict=True)
    msg = str(exc.value)
    assert "Ellipsis" in msg
    assert "final argument" in msg
