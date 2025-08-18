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
