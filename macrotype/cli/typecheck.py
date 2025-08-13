from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from .. import stubgen
from . import DEFAULT_OUT_DIR, _default_output_path
from .watch import watch_and_run


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
    cli_argv = argv[:dash]

    parser = argparse.ArgumentParser(prog="macrotype-check")
    parser.add_argument("tool")
    parser.add_argument("paths", nargs="+")
    parser.add_argument("-o", "--output", default=str(DEFAULT_OUT_DIR))
    parser.add_argument(
        "-w",
        "--watch",
        action="store_true",
        help="Watch for changes and re-run the checker",
    )
    args = parser.parse_args(cli_argv)

    command = "macrotype-check " + " ".join(cli_argv + (["--"] + tool_args if tool_args else []))

    if args.watch:
        cmd = [
            sys.executable,
            "-m",
            "macrotype.cli.typecheck",
            *[a for a in cli_argv if a not in {"-w", "--watch"}],
        ]
        if tool_args:
            cmd += ["--", *tool_args]
        return watch_and_run(args.paths, cmd)

    out_dir = Path(args.output)
    stub_paths = _generate_stubs(args.paths, out_dir, command)

    env = os.environ.copy()
    stub_path = str(out_dir)
    env_path = "MYPYPATH" if args.tool == "mypy" else "PYTHONPATH"
    env[env_path] = stub_path + os.pathsep + env.get(env_path, "")

    cmd = [args.tool, *map(str, stub_paths), *tool_args]
    result = subprocess.run(cmd, env=env)
    return result.returncode


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
