import sys
from pathlib import Path
import subprocess


def test_cli_stdout(tmp_path):
    expected = Path(__file__).with_name("all_annotations.pyi").read_text()
    result = subprocess.run(
        [sys.executable, "-m", "macrotype", str(Path(__file__).with_name("all_annotations.py")), "-o", "-"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[1],
        check=True,
    )
    assert result.stdout.strip().splitlines() == expected.strip().splitlines()
