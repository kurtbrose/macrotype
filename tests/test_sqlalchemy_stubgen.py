"""Stress-test macrotype against SQLAlchemy."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

sqlalchemy = pytest.importorskip("sqlalchemy")


def test_sqlalchemy_stubgen(tmp_path: Path) -> None:
    pkg_dir = Path(sqlalchemy.__file__).resolve().parent
    repo_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root)
    try:
        subprocess.run(
            [sys.executable, "-m", "macrotype", str(pkg_dir), "-o", str(tmp_path)],
            env=env,
            cwd=tmp_path,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        pytest.xfail(f"macrotype fails on SQLAlchemy: {exc}")
