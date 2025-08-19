import sys
from pathlib import Path

import pytest

from macrotype.modules.ir import SourceInfo
from macrotype.modules.source import extract_source_info
from macrotype.stubgen import load_module, stub_lines
from macrotype.types.validate import TypeValidationError


def test_invalid_literal_error():
    path = Path(__file__).with_name("annotations_invalid.py")
    mod = load_module("tests.annotations_invalid")
    header, comments, line_map = extract_source_info(path.read_text())
    info = SourceInfo(headers=header, comments=comments, line_map=line_map)
    with pytest.raises(TypeValidationError) as exc:
        stub_lines(mod, source_info=info, strict=True)
    msg = str(exc.value)
    assert "Illegal Literal value" in msg
    assert "Literal" in msg
    sys.modules.pop("tests.annotations_invalid", None)


def test_invalid_non_type_error():
    path = Path(__file__).with_name("annotations_invalid_non_type.py")
    mod = load_module("tests.annotations_invalid_non_type")
    header, comments, line_map = extract_source_info(path.read_text())
    info = SourceInfo(headers=header, comments=comments, line_map=line_map)
    lines = stub_lines(mod, source_info=info, strict=True)
    assert lines[-1] == "BAD_NON_TYPE: 123"
    sys.modules.pop("tests.annotations_invalid_non_type", None)


def test_unresolved_string_kept_as_name(tmp_path):
    code = 'X: "Missing"\n'
    path = tmp_path / "unresolved_mod.py"
    path.write_text(code)
    sys.path.insert(0, str(tmp_path))
    try:
        mod = load_module("unresolved_mod")
    finally:
        sys.path.remove(str(tmp_path))
        sys.modules.pop("unresolved_mod", None)
    header, comments, line_map = extract_source_info(code)
    info = SourceInfo(headers=header, comments=comments, line_map=line_map)
    lines = stub_lines(mod, source_info=info, strict=True)
    assert lines == ["X: Missing"]


def test_forward_ref_kept_as_name(tmp_path):
    code = 'import typing\nX: typing.ForwardRef("Missing")\n'
    path = tmp_path / "forward_ref_mod.py"
    path.write_text(code)
    sys.path.insert(0, str(tmp_path))
    try:
        mod = load_module("forward_ref_mod")
    finally:
        sys.path.remove(str(tmp_path))
        sys.modules.pop("forward_ref_mod", None)
    header, comments, line_map = extract_source_info(code)
    info = SourceInfo(headers=header, comments=comments, line_map=line_map)
    lines = stub_lines(mod, source_info=info, strict=True)
    assert lines[0] == "from typing import Missing"
    assert lines[-1] == "X: Missing"


def test_misplaced_ellipsis_in_tuple_raises_error() -> None:
    path = Path(__file__).with_name("strict_error.py")
    mod = load_module("tests.strict_error")
    header, comments, line_map = extract_source_info(path.read_text())
    info = SourceInfo(headers=header, comments=comments, line_map=line_map)
    with pytest.raises(TypeValidationError) as exc:
        stub_lines(mod, source_info=info, strict=True)
    msg = str(exc.value)
    assert "Ellipsis" in msg
    assert "final argument" in msg
    sys.modules.pop("tests.strict_error", None)
