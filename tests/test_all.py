import io
import re
import subprocess
import sys
import tokenize
from pathlib import Path

import pytest

# Ensure the package root is on sys.path when running tests directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from macrotype import stubgen
from macrotype.stubgen import load_module_from_path, process_directory, process_file

CASES = [
    ("annotations.py", "annotations.pyi", False),
    ("annotations_new.py", "annotations_new.pyi", True),
    pytest.param(
        "annotations_13.py",
        "annotations_13.pyi",
        False,
        marks=pytest.mark.skipif(sys.version_info < (3, 13), reason="requires Python 3.13+"),
    ),
]


@pytest.mark.parametrize("src, expected, use_modules", CASES)
def test_cli_stdout(tmp_path, src: str, expected: str, use_modules: bool) -> None:
    expected_path = Path(__file__).with_name(expected)
    expected_lines = expected_path.read_text().splitlines()
    flag = " --modules" if use_modules else ""
    expected_lines[0] = f"# Generated via: macrotype {expected_path.with_name(src)}{flag} -o -"
    if use_modules:
        expected_lines = [line for line in expected_lines if line != "# fmt: off"]
    cmd = [sys.executable, "-m", "macrotype", str(Path(__file__).with_name(src))]
    if use_modules:
        cmd.append("--modules")
    cmd += ["-o", "-"]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[1],
        check=True,
    )
    assert result.stdout.strip().splitlines() == expected_lines


@pytest.mark.parametrize("src, expected, use_modules", CASES)
def test_stub_generation_matches_expected(src: str, expected: str, use_modules: bool) -> None:
    src_path = Path(__file__).with_name(src)
    sys.modules.pop(src_path.stem, None)
    sys.modules.pop(f"tests.{src_path.stem}", None)
    loaded = load_module_from_path(src_path)
    generated = stubgen.stub_lines(loaded, use_modules=use_modules, strict=use_modules)

    expected_path = Path(__file__).with_name(expected)
    expected_lines = expected_path.read_text().splitlines()[2:]
    if use_modules:
        expected_lines = [line for line in expected_lines if line != "# fmt: off"]

    assert generated == expected_lines


@pytest.mark.parametrize("src, expected, use_modules", CASES)
def test_process_file(tmp_path, src: str, expected: str, use_modules: bool) -> None:
    src_path = Path(__file__).with_name(src)
    sys.modules.pop(src_path.stem, None)
    sys.modules.pop(f"tests.{src_path.stem}", None)
    dest = tmp_path / f"out_{src_path.stem}.pyi"
    process_file(src_path, dest, use_modules=use_modules, strict=use_modules)
    expected_lines = Path(__file__).with_name(expected).read_text().splitlines()[2:]
    if use_modules:
        expected_lines = [line for line in expected_lines if line != "# fmt: off"]
    assert dest.read_text().splitlines() == expected_lines


@pytest.mark.parametrize("src, expected, use_modules", CASES)
def test_process_directory(tmp_path, src: str, expected: str, use_modules: bool) -> None:
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src_path = Path(__file__).with_name(src)
    dest_src = src_dir / src_path.name
    dest_src.write_text(src_path.read_text())
    process_directory(src_dir, tmp_path, use_modules=use_modules, strict=use_modules)
    generated = (tmp_path / expected).read_text().splitlines()
    expected_lines = Path(__file__).with_name(expected).read_text().splitlines()[2:]
    if use_modules:
        expected_lines = [line for line in expected_lines if line != "# fmt: off"]
    assert generated == expected_lines


def test_process_directory_skips_dunder_main(tmp_path) -> None:
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("# pkg init\n")
    sub = pkg / "sub"
    sub.mkdir()
    (sub / "__init__.py").write_text("# sub init\n")
    (sub / "__main__.py").write_text("raise RuntimeError('should not import')\n")
    (sub / "mod.py").write_text("X = 1\n")

    out = tmp_path / "out"
    process_directory(pkg, out)
    names = {p.name for p in out.iterdir()}
    assert "mod.pyi" in names
    assert "__main__.pyi" not in names


def test_module_alias(tmp_path) -> None:
    import pathlib

    from macrotype.meta_types import set_module

    original = pathlib.Path.__module__
    set_module(pathlib.Path, "pathlib._local")
    try:
        src_path = Path(__file__).with_name("annotations_new.py")
        loaded = load_module_from_path(src_path)
        lines = stubgen.stub_lines(loaded, use_modules=True, strict=True)
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
