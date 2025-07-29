import subprocess
import sys
from pathlib import Path

import pytest

CHECKERS = ["mypy", "pyright"]


@pytest.mark.parametrize("checker", CHECKERS)
def test_stub_files_pass(checker: str) -> None:
    pyi_dir = Path(__file__).parent
    # these stubs rely on PEP 695-style generics and fail on current checkers
    # mypy will also load annotations.pyi when analyzing typechecking.pyi
    skip = {"annotations_13.pyi", "annotations_pep_695.pyi", "typechecking.pyi"}
    for path in sorted(pyi_dir.glob("*.pyi")):
        if path.name in skip:
            continue
        result = subprocess.run(
            [sys.executable, "-m", checker, str(path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
