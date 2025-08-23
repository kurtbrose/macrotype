import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("tool", ["mypy", "pyright"])
def test_generated_stub_typechecks(tmp_path: Path, tool: str) -> None:
    src = tmp_path / "mod.py"
    src.write_text(
        """
from typing import overload

@overload
def identity(x: int) -> int: ...
@overload
def identity(x: str) -> str: ...
def identity(x: int | str) -> int | str:
    return x
"""
    )
    repo_root = Path(__file__).resolve().parents[1]
    stub_dir = tmp_path / "stubs"
    cmd = [
        sys.executable,
        "-m",
        "macrotype.cli.typecheck",
        tool,
        "mod.py",
        "-o",
        str(stub_dir),
        "--",
    ]
    env = os.environ.copy()
    stub_path = repo_root / "__macrotype__"
    env["MYPYPATH"] = str(stub_path) + os.pathsep + env.get("MYPYPATH", "")
    env["PYTHONPATH"] = (
        str(repo_root) + os.pathsep + str(stub_path) + os.pathsep + env.get("PYTHONPATH", "")
    )
    result = subprocess.run(
        cmd,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
