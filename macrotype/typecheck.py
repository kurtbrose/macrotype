from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from . import stubgen
from .cli import DEFAULT_OUT_DIR, _default_output_path


def _generate_stubs(paths: list[str], out_dir: Path, command: str) -> list[Path]:
    cwd = Path.cwd()
    outputs: list[Path] = []
    for target in paths:
        path = Path(target)
        default = _default_output_path(path, cwd, is_file=path.is_file())
        rel = default.relative_to(DEFAULT_OUT_DIR)
        dest = out_dir / rel
        if path.is_file():
            outputs.append(stubgen.process_file(path, dest, command=command))
        else:
            stubgen.process_directory(path, dest, command=command)
            outputs.append(dest)
    return outputs


def main(argv: list[str] | None = None) -> int:
    argv = list(argv or sys.argv[1:])
    try:
        dash = argv.index("--")
    except ValueError:
        dash = len(argv)
    tool_args = argv[dash + 1 :]
    argv = argv[:dash]

    parser = argparse.ArgumentParser(prog="macrotype-check")
    parser.add_argument("tool")
    parser.add_argument("paths", nargs="+")
    parser.add_argument("-o", "--output", default=str(DEFAULT_OUT_DIR))
    args = parser.parse_args(argv)

    command = "macrotype-check " + " ".join(argv + (["--"] + tool_args if tool_args else []))
    out_dir = Path(args.output)
    stub_paths = _generate_stubs(args.paths, out_dir, command)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(out_dir) + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run([args.tool, *map(str, stub_paths), *tool_args], env=env)
    return result.returncode


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
