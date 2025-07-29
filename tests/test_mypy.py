import subprocess
import sys
from pathlib import Path

import pytest


_SKIP = {"annotations_unsupported.pyi", "annotations_13.pyi", "typechecking.pyi"}


def _pyi_files() -> list[Path]:
    pyi_dir = Path(__file__).parent
    return [p for p in sorted(pyi_dir.glob("*.pyi")) if p.name not in _SKIP]


@pytest.mark.parametrize("tool", ["mypy", "pyright"])
@pytest.mark.parametrize("pyi_file", _pyi_files(), ids=lambda p: p.name)
def test_stubs_pass_typecheck(pyi_file: Path, tool: str) -> None:
    if tool == "mypy":
        cmd = [sys.executable, "-m", "mypy", str(pyi_file)]
    else:
        cmd = [tool, str(pyi_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
