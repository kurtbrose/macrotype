import subprocess
import sys
from pathlib import Path

# Ensure package root on path when running tests directly
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

STUBS_DIR = Path(__file__).resolve().parents[1] / "stubs"


def test_cli_self(tmp_path: Path) -> None:
    repo_root = STUBS_DIR.parent
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
