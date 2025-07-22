import sys
from pathlib import Path
import subprocess
import pytest


def test_cli_stdout(tmp_path):
    expected = Path(__file__).with_name("annotations.pyi").read_text()
    result = subprocess.run(
        [sys.executable, "-m", "macrotype", str(Path(__file__).with_name("annotations.py")), "-o", "-"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[1],
        check=True,
    )
    assert result.stdout.strip().splitlines() == expected.strip().splitlines()


@pytest.mark.skipif(sys.version_info < (3, 13), reason="requires Python 3.13+")
def test_cli_stdout_py313(tmp_path):
    expected = Path(__file__).with_name("annotations_13.pyi").read_text()
    result = subprocess.run(
        [sys.executable, "-m", "macrotype", str(Path(__file__).with_name("annotations_13.py")), "-o", "-"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[1],
        check=True,
    )
    assert result.stdout.strip().splitlines() == expected.strip().splitlines()
