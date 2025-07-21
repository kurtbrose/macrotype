from pathlib import Path

from macrotype.stubgen import process_file, process_directory


def test_process_file(tmp_path):
    src = Path(__file__).with_name("all_annotations.py")
    dest = tmp_path / "out.pyi"
    process_file(src, dest)
    expected = Path(__file__).with_name("all_annotations.pyi").read_text().splitlines()
    assert dest.read_text().splitlines() == expected


def test_process_directory(tmp_path):
    src_dir = Path(__file__).parent
    process_directory(src_dir, tmp_path)
    generated = (tmp_path / "all_annotations.pyi").read_text().splitlines()
    expected = Path(__file__).with_name("all_annotations.pyi").read_text().splitlines()
    assert generated == expected
