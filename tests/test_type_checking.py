from pathlib import Path

import pytest

from macrotype.modules.ir import SourceInfo
from macrotype.modules.source import extract_source_info
from macrotype.stubgen import load_module, stub_lines


def test_skip_type_checking() -> None:
    path = Path(__file__).with_name("typechecking.py")
    with pytest.raises(RuntimeError):
        load_module("tests.typechecking")


def test_allow_type_checking_generates_runtime_stub() -> None:
    path = Path(__file__).with_name("typechecking.py")
    code = path.read_text()
    mod = load_module("tests.typechecking", allow_type_checking=True)
    header, comments, line_map, tc_imports = extract_source_info(code, allow_type_checking=True)
    info = SourceInfo(
        headers=header,
        comments=comments,
        line_map=line_map,
        tc_imports=tc_imports,
    )
    lines = stub_lines(mod, source_info=info, strict=True)
    expected = Path(__file__).with_name("typechecking.pyi").read_text().splitlines()
    assert lines == expected


def test_simple_type_checking_imports() -> None:
    path = Path(__file__).with_name("typechecking_import_only.py")
    code = path.read_text()
    mod = load_module("tests.typechecking_import_only")
    header, comments, line_map, tc_imports = extract_source_info(code)
    info = SourceInfo(
        headers=header,
        comments=comments,
        line_map=line_map,
        tc_imports=tc_imports,
    )
    lines = stub_lines(mod, source_info=info, strict=True)
    expected = Path(__file__).with_name("typechecking_import_only.pyi").read_text().splitlines()
    assert lines == expected
