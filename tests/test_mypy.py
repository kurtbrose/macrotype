import subprocess
import sys
from pathlib import Path


def test_stub_files_pass_mypy():
    pyi_dir = Path(__file__).parent
    pyi_paths = sorted(pyi_dir.glob("*.pyi"))
    skip = {"annotations.pyi", "annotations_13.pyi", "typechecking.pyi"}
    pyi_paths = [p for p in pyi_paths if p.name not in skip]
    for path in pyi_paths:
        result = subprocess.run(
            [sys.executable, "-m", "mypy", str(path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
