import os
import subprocess
import sys
from pathlib import Path

import pytest


def _check_overlay(stub_dir: Path, dest: Path) -> None:
    overlay = stub_dir / "tests" / "annotations_new.pyi"
    assert overlay.exists()
    if overlay.is_symlink():
        assert overlay.resolve() == dest.resolve()
    else:  # pragma: no cover - fallback for platforms without symlink
        assert overlay.read_text() == dest.read_text()


@pytest.mark.parametrize("overlay_subdir", [None, "stubs"])
def test_cli_stub_overlay_dir(tmp_path, overlay_subdir):
    repo_root = Path(__file__).resolve().parents[1]
    src = Path(__file__).with_name("annotations_new.py")
    dest = tmp_path / "annotations_new.pyi"
    args = [
        sys.executable,
        "-m",
        "macrotype",
        str(src),
        "-o",
        str(dest),
    ]
    stub_dir = tmp_path / overlay_subdir if overlay_subdir else tmp_path
    if overlay_subdir:
        args.extend(["--stub-overlay-dir", str(stub_dir)])
    subprocess.run(args, check=True, cwd=repo_root)
    if overlay_subdir:
        _check_overlay(stub_dir, dest)
    else:
        assert not (stub_dir / "tests" / "annotations_new.pyi").exists()


def test_cli_stub_overlay_dir_with_subpackage(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    pkg = tmp_path / "pkg"
    subpkg = pkg / "sub"
    subpkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (pkg / "a.py").write_text("a = 1\n")
    (subpkg / "__init__.py").write_text("")
    (subpkg / "b.py").write_text("b = 2\n")
    out_dir = tmp_path / "out"
    stub_dir = tmp_path / "stubs"
    env = os.environ | {"PYTHONPATH": str(repo_root)}
    subprocess.run(
        [
            sys.executable,
            "-m",
            "macrotype",
            "pkg",
            "-o",
            str(out_dir),
            "--stub-overlay-dir",
            str(stub_dir),
        ],
        check=True,
        cwd=tmp_path,
        env=env,
    )
    overlay = stub_dir / "pkg" / "sub" / "b.pyi"
    dest = out_dir / "sub" / "b.pyi"
    assert overlay.exists()
    if overlay.is_symlink():
        assert overlay.resolve() == dest.resolve()
    else:  # pragma: no cover - fallback for platforms without symlink
        assert overlay.read_text() == dest.read_text()
