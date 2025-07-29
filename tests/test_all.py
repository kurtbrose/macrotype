import subprocess
import sys
from pathlib import Path
import io
import re
import tokenize

import pytest

# Ensure the package root is on sys.path when running tests directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from macrotype.pyi_extract import PyiModule
from macrotype.stubgen import load_module_from_path, process_directory, process_file

CASES = [
    ("annotations.py", "annotations.pyi"),
    pytest.param(
        "annotations_13.py",
        "annotations_13.pyi",
        marks=pytest.mark.skipif(sys.version_info < (3, 13), reason="requires Python 3.13+"),
    ),
]


@pytest.mark.parametrize("src, expected", CASES)
def test_cli_stdout(tmp_path, src: str, expected: str) -> None:
    expected_path = Path(__file__).with_name(expected)
    expected_lines = expected_path.read_text().splitlines()
    expected_lines[0] = f"# Generated via: macrotype {expected_path.with_name(src)} -o -"
    result = subprocess.run(
        [sys.executable, "-m", "macrotype", str(Path(__file__).with_name(src)), "-o", "-"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[1],
        check=True,
    )
    assert result.stdout.strip().splitlines() == expected_lines


@pytest.mark.parametrize("src, expected", CASES)
def test_stub_generation_matches_expected(src: str, expected: str) -> None:
    src_path = Path(__file__).with_name(src)
    loaded = load_module_from_path(src_path)
    module = PyiModule.from_module(loaded)
    generated = module.render()

    expected_path = Path(__file__).with_name(expected)
    expected_lines = expected_path.read_text().splitlines()[2:]

    assert generated == expected_lines


@pytest.mark.parametrize("src, expected", CASES)
def test_process_file(tmp_path, src: str, expected: str) -> None:
    src_path = Path(__file__).with_name(src)
    dest = tmp_path / f"out_{src_path.stem}.pyi"
    process_file(src_path, dest)
    expected_lines = Path(__file__).with_name(expected).read_text().splitlines()[2:]
    assert dest.read_text().splitlines() == expected_lines


@pytest.mark.parametrize("src, expected", CASES)
def test_process_directory(tmp_path, src: str, expected: str) -> None:
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src_path = Path(__file__).with_name(src)
    dest_src = src_dir / src_path.name
    dest_src.write_text(src_path.read_text())
    process_directory(src_dir, tmp_path)
    generated = (tmp_path / expected).read_text().splitlines()
    expected_lines = Path(__file__).with_name(expected).read_text().splitlines()[2:]
    assert generated == expected_lines


def test_module_alias(tmp_path) -> None:
    import pathlib

    from macrotype.meta_types import set_module

    original = pathlib.Path.__module__
    set_module(pathlib.Path, "pathlib._local")
    try:
        src_path = Path(__file__).with_name("annotations.py")
        loaded = load_module_from_path(src_path)
        module = PyiModule.from_module(loaded)
        lines = module.render()
    finally:
        set_module(pathlib.Path, original)

    assert any(line == "from pathlib import Path" for line in lines)


def test_pyi_comments_match_source() -> None:
    src = Path(__file__).with_name("annotations.py")
    pyi = Path(__file__).with_name("annotations.pyi")
    pattern = re.compile(r"#\s*(?:type:|pyright:|mypy:|pyre-|pyre:)")

    def _grab(text: str) -> list[str]:
        return [
            tok_str
            for tok_type, tok_str, *_ in tokenize.generate_tokens(io.StringIO(text).readline)
            if tok_type == tokenize.COMMENT and pattern.match(tok_str)
        ]

    assert _grab(src.read_text()) == _grab(pyi.read_text())
