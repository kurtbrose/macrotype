import os
import subprocess
import sys
from pathlib import Path

import pytest
import sqlalchemy


@pytest.mark.skip(reason="stub generation for SQLAlchemy is currently too slow")
def test_cli_sqlalchemy(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sa_dir = Path(sqlalchemy.__file__).resolve().parent
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root)
    output = tmp_path / "sqlalchemy.pyi"
    subprocess.run(
        [sys.executable, "-m", "macrotype", "__init__.py", "-o", str(output)],
        cwd=sa_dir,
        env=env,
        check=True,
    )
    assert output.exists()
