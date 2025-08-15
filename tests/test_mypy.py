import subprocess
import sys
from pathlib import Path

import pytest

_SKIP = {
    "annotations_unsupported.pyi",
    "annotations_13.pyi",
    "annotations.pyi",
    "typechecking.pyi",
    "strict_error.pyi",
}


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


TYPES_AST_FILE = Path(__file__).with_name("types_ast_typing.py")


@pytest.mark.parametrize("tool", ["mypy", "pyright"])
def test_types_ast_types(tool: str) -> None:
    if tool == "mypy":
        cmd = [sys.executable, "-m", "mypy", "--follow-imports=skip", str(TYPES_AST_FILE)]
    else:
        cmd = [tool, str(TYPES_AST_FILE)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
