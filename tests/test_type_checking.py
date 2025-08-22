from pathlib import Path

import pytest

from macrotype.modules.source import extract_source_info
from macrotype.stubgen import load_module, stub_lines


def _strip_comments(lines: list[str]) -> list[str]:
    result = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        if "#" in line:
            line = line.split("#", 1)[0].rstrip()
        result.append(line)
    return result


def test_skip_type_checking() -> None:
    path = Path(__file__).with_name("typechecking.py")
    with pytest.raises(RuntimeError):
        load_module("tests.typechecking")


def test_allow_type_checking_generates_runtime_stub() -> None:
    path = Path(__file__).with_name("typechecking.py")
    code = path.read_text()
    mod = load_module("tests.typechecking", allow_type_checking=True)
    info = extract_source_info(code, allow_type_checking=True)
    lines = stub_lines(mod, source_info=info, strict=True)
    expected = Path(__file__).with_name("typechecking.pyi").read_text().splitlines()
    assert _strip_comments(lines) == _strip_comments(expected)


def test_simple_type_checking_imports() -> None:
    path = Path(__file__).with_name("typechecking_import_only.py")
    code = path.read_text()
    mod = load_module("tests.typechecking_import_only")
    info = extract_source_info(code)
    lines = stub_lines(mod, source_info=info, strict=True)
    expected = Path(__file__).with_name("typechecking_import_only.pyi").read_text().splitlines()
    assert _strip_comments(lines) == _strip_comments(expected)


def test_alias_type_checking_imports() -> None:
    path = Path(__file__).with_name("typechecking_alias.py")
    code = path.read_text()
    mod = load_module("tests.typechecking_alias")
    info = extract_source_info(code)
    lines = stub_lines(mod, source_info=info, strict=True)
    expected = Path(__file__).with_name("typechecking_alias.pyi").read_text().splitlines()
    assert _strip_comments(lines) == _strip_comments(expected)
