import subprocess
import sys
from pathlib import Path

import pytest

CHECKERS = ["mypy", "pyright"]


def _stub_paths() -> list[Path]:
    pyi_dir = Path(__file__).parent
    skip = {"annotations.pyi", "annotations_13.pyi", "typechecking.pyi"}
    return [p for p in sorted(pyi_dir.glob("*.pyi")) if p.name not in skip]


@pytest.mark.parametrize("checker", CHECKERS)
def test_stub_files_pass(checker: str) -> None:
    for path in _stub_paths():
        result = subprocess.run(
            [sys.executable, "-m", checker, str(path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
