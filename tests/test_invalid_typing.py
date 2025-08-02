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
