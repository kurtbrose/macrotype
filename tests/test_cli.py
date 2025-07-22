import sys
from pathlib import Path
import subprocess
import sys
import pytest


cases = [
    ("annotations.py", "annotations.pyi"),
    pytest.param(
        "annotations_13.py",
        "annotations_13.pyi",
        marks=pytest.mark.skipif(sys.version_info < (3, 13), reason="requires Python 3.13+"),
    ),
]

@pytest.mark.parametrize("src, expected", cases)
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
