# Generated via: macrotype macrotype/watch.py -o __macrotype__/macrotype/watch.pyi
# Do not edit by hand
from collections.abc import Iterable
from pathlib import Path
from threading import Event

def _snapshot(paths: Iterable[Path]) -> dict[Path, float]: ...

def watch_and_run(paths: Iterable[str | Path], cmd: list[str], *, interval: float, stop_event: Event | None, cwd: Path | None, env: dict[str, str] | None) -> int: ...
