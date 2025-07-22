from pathlib import Path
import sys
import pytest

from macrotype.stubgen import process_file, process_directory


CASES = [
    ("annotations.py", "annotations.pyi"),
    pytest.param(
        "annotations_13.py",
        "annotations_13.pyi",
        marks=pytest.mark.skipif(sys.version_info < (3, 13), reason="requires Python 3.13+"),
    ),
]


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
