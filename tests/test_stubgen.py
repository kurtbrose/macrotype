from pathlib import Path
import sys
import pytest

from macrotype.stubgen import process_file, process_directory


def test_process_file(tmp_path):
    src = Path(__file__).with_name("annotations.py")
    dest = tmp_path / "out.pyi"
    process_file(src, dest)
    expected = Path(__file__).with_name("annotations.pyi").read_text().splitlines()
    assert dest.read_text().splitlines() == expected


def test_process_directory(tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src = Path(__file__).with_name("annotations.py")
    dest_src = src_dir / src.name
    dest_src.write_text(src.read_text())
    process_directory(src_dir, tmp_path)
    generated = (tmp_path / "annotations.pyi").read_text().splitlines()
    expected = Path(__file__).with_name("annotations.pyi").read_text().splitlines()
    assert generated == expected


@pytest.mark.skipif(sys.version_info < (3, 13), reason="requires Python 3.13+")
def test_process_file_py313(tmp_path):
    src = Path(__file__).with_name("annotations_13.py")
    dest = tmp_path / "out_13.pyi"
    process_file(src, dest)
    expected = Path(__file__).with_name("annotations_13.pyi").read_text().splitlines()
    assert dest.read_text().splitlines() == expected


@pytest.mark.skipif(sys.version_info < (3, 13), reason="requires Python 3.13+")
def test_process_directory_py313(tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src = Path(__file__).with_name("annotations_13.py")
    dest_src = src_dir / src.name
    dest_src.write_text(src.read_text())
    process_directory(src_dir, tmp_path)
    generated = (tmp_path / "annotations_13.pyi").read_text().splitlines()
    expected = Path(__file__).with_name("annotations_13.pyi").read_text().splitlines()
    assert generated == expected
