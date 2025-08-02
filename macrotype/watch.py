from __future__ import annotations

import subprocess
import time
from pathlib import Path
from threading import Event
from typing import Iterable

from . import stubgen


def _snapshot(paths: Iterable[Path]) -> dict[Path, float]:
    files: list[Path] = []
    for p in paths:
        files.extend(stubgen.iter_python_files(p))
    return {f: f.stat().st_mtime for f in files if f.exists()}


def watch_and_run(
    paths: Iterable[str | Path],
    cmd: list[str],
    *,
    interval: float = 0.5,
    stop_event: Event | None = None,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> int:
    """Run *cmd* and watch *paths* for changes.

    When any ``.py`` file under ``paths`` changes, ``cmd`` is executed again.
    If ``stop_event`` is provided, the loop terminates when the event is set.
    """

    path_objs = [Path(p) for p in paths]

    def run() -> int:
        return subprocess.run(cmd, check=False, cwd=cwd, env=env).returncode

    code = run()
    mtimes = _snapshot(path_objs)
    print("Watching for changes. Press Ctrl+C to exit.")
    try:
        while True:
            if stop_event and stop_event.is_set():
                break
            time.sleep(interval)
            new = _snapshot(path_objs)
            if new != mtimes:
                mtimes = new
                code = run()
    except KeyboardInterrupt:
        pass
    return code


__all__ = ["watch_and_run"]
