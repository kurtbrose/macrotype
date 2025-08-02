import os
import subprocess
import sys
import sysconfig
from pathlib import Path

# Ensure package root on path when running tests directly
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

STUBS_DIR = Path(__file__).resolve().parents[1] / "__macrotype__" / "macrotype"


def test_cli_self(tmp_path: Path) -> None:
    repo_root = STUBS_DIR.parents[1]
    subprocess.run(
        [sys.executable, "-m", "macrotype", "macrotype", "-o", str(tmp_path)],
        cwd=repo_root,
        check=True,
    )
    for stub in STUBS_DIR.glob("*.pyi"):
        generated = (tmp_path / stub.name).read_text().splitlines()
        expected = stub.read_text().splitlines()
        expected[0] = f"# Generated via: macrotype macrotype -o {tmp_path}"
        assert generated == expected


def test_cli_default_output_dir(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    src = pkg / "mod.py"
    src.write_text("VAL = 1\n")

    repo_root = STUBS_DIR.parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "macrotype",
            "pkg",
        ],
        cwd=tmp_path,
        env=env,
        check=True,
    )

    stub = tmp_path / "__macrotype__" / "pkg" / "mod.pyi"
    expected_lines = [
        "# Generated via: macrotype pkg",
        "# Do not edit by hand",
        "VAL: int",
    ]
    assert stub.read_text().splitlines() == expected_lines


def test_cli_requires_relative_path(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside"
    outside.mkdir()
    src = outside / "mod.py"
    src.write_text("X = 1\n")

    repo_root = STUBS_DIR.parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root)
    result = subprocess.run(
        [sys.executable, "-m", "macrotype", str(src)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "specify -o" in result.stderr


def test_cli_stdlib(tmp_path: Path) -> None:
    repo_root = STUBS_DIR.parents[1]
    stdlib = Path(sysconfig.get_path("stdlib"))
    site_pkgs = stdlib / "site-packages"
    renamed = None
    if site_pkgs.exists():
        renamed = stdlib / "site-packages_tmp"
        site_pkgs.rename(renamed)
    try:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root)
        subprocess.run(
            [sys.executable, "-m", "macrotype", ".", "-o", str(tmp_path)],
            cwd=stdlib,
            env=env,
            check=True,
        )
    finally:
        if renamed:
            renamed.rename(site_pkgs)
