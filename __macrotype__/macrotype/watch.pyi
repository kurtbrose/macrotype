# Generated via: macrotype macrotype -o __macrotype__/macrotype
# Do not edit by hand
from collections.abc import Iterable
from pathlib import Path
from threading import Event

def _snapshot(paths: Iterable[Path]) -> dict[Path, float]: ...

def watch_and_run(paths: Iterable[Path | str], cmd: list[str], *, interval: float, stop_event: Event | None, cwd: None | Path, env: None | dict[str, str]) -> int: ...
