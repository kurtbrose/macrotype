import os
import sys
import threading
import time
from pathlib import Path

from macrotype.watch import watch_and_run


def test_watch_and_run_regenerates(tmp_path: Path) -> None:
    src = tmp_path / "m.py"
    src.write_text("a=1\n")
    dest = tmp_path / "out.pyi"
    cmd = [
        sys.executable,
        "-m",
        "macrotype",
        str(src),
        "-o",
        str(dest),
    ]
    env = os.environ | {"PYTHONPATH": str(Path(__file__).resolve().parents[1])}
    stop = threading.Event()
    thread = threading.Thread(
        target=watch_and_run,
        args=([src], cmd),
        kwargs={"interval": 0.1, "stop_event": stop, "cwd": tmp_path, "env": env},
        daemon=True,
    )
    thread.start()
    try:
        for _ in range(50):
            if dest.exists():
                break
            time.sleep(0.1)
        assert dest.exists()
        assert "a: int" in dest.read_text()

        time.sleep(1)
        src.write_text("b=1\n")
        old = dest.read_text()
        for _ in range(50):
            time.sleep(0.1)
            if dest.read_text() != old:
                break
        assert "b: int" in dest.read_text()
    finally:
        stop.set()
        thread.join(5)
