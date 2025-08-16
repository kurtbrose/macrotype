import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("tool", ["mypy", "pyright"])
def test_macrotype_check(tmp_path: Path, tool: str) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    stub_dir = tmp_path / "stubs"
    cmd = [
        sys.executable,
        "-m",
        "macrotype.cli.typecheck",
        tool,
        "tests/annotations_new.py",
        "-o",
        str(stub_dir),
        "--",
    ]
    result = subprocess.run(
        cmd,
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=os.environ,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (stub_dir / "tests" / "annotations_new.pyi").exists()
