# Generated via: macrotype macrotype
# Do not edit by hand
from __future__ import annotations
from pathlib import Path
from threading import Event

from typing import Iterable

def _snapshot(paths: Iterable[Path]) -> dict[Path, float]: ...

def watch_and_run(paths: Iterable[Path | str], cmd: list[str], interval: float, stop_event: Event | None, cwd: None | Path, env: None | dict[str, str]) -> int: ...
