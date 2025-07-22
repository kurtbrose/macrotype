import sys
import subprocess
from pathlib import Path
import pytest

# Ensure the package root is on sys.path when running tests directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from macrotype.pyi_extract import PyiModule
from macrotype.stubgen import load_module_from_path, process_file, process_directory

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
    expected_text = Path(__file__).with_name(expected).read_text()
    result = subprocess.run(
        [sys.executable, "-m", "macrotype", str(Path(__file__).with_name(src)), "-o", "-"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[1],
        check=True,
    )
    assert result.stdout.strip().splitlines() == expected_text.strip().splitlines()


@pytest.mark.parametrize("src, expected", CASES)
def test_stub_generation_matches_expected(src: str, expected: str) -> None:
    src_path = Path(__file__).with_name(src)
    loaded = load_module_from_path(src_path)
    module = PyiModule.from_module(loaded)
    generated = module.render()

    expected_path = Path(__file__).with_name(expected)
    expected_lines = expected_path.read_text().splitlines()

    assert generated == expected_lines


@pytest.mark.parametrize("src, expected", CASES)
def test_process_file(tmp_path, src: str, expected: str) -> None:
    src_path = Path(__file__).with_name(src)
    dest = tmp_path / f"out_{src_path.stem}.pyi"
    process_file(src_path, dest)
    expected_lines = Path(__file__).with_name(expected).read_text().splitlines()
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
    expected_lines = Path(__file__).with_name(expected).read_text().splitlines()
    assert generated == expected_lines


def test_mixed_typeddict_support() -> None:
    src_path = Path(__file__).with_name("annotations.py")
    loaded = load_module_from_path(src_path)
    module = PyiModule.from_module(loaded)
    lines = module.render()
    assert "class MixedDict(TypedDict):" in lines
    assert "    optional_field: NotRequired[str]" in lines
    assert "    required_override: Required[int]" in lines
