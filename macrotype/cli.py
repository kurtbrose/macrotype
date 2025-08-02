from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import stubgen
from .watch import watch_and_run

DEFAULT_OUT_DIR = Path("__macrotype__")


def _default_output_path(path: Path, cwd: Path, *, is_file: bool) -> Path:
    """Return the default output location for ``path`` relative to ``cwd``."""

    abs_path = path if path.is_absolute() else cwd / path
    if not abs_path.is_relative_to(cwd):
        raise ValueError(f"{path} is not under {cwd}; specify -o")
    rel = abs_path.relative_to(cwd)
    base = DEFAULT_OUT_DIR / rel
    return base.with_suffix(".pyi") if is_file else base


def _stdout_write(lines: list[str], command: str | None = None) -> None:
    sys.stdout.write("\n".join(stubgen._header_lines(command) + lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    argv = list(argv or sys.argv[1:])
    parser = argparse.ArgumentParser(prog="macrotype")
    parser.add_argument(
        "paths",
        nargs="*",
        default=["-"],
        help="Files or directories to process or '-' for stdin/stdout",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output directory or file. Use '-' for stdout when processing a single file or stdin.",
    )
    parser.add_argument(
        "-w",
        "--watch",
        action="store_true",
        help="Watch for changes and regenerate stubs",
    )
    args = parser.parse_args(argv)
    command = "macrotype " + " ".join(argv)

    if args.watch:
        if args.paths == ["-"]:
            parser.error("--watch cannot be used with stdin")
        cmd = [
            sys.executable,
            "-m",
            "macrotype",
            *[a for a in argv if a not in {"-w", "--watch"}],
        ]
        return watch_and_run(args.paths, cmd)

    if args.paths == ["-"]:
        code = sys.stdin.read()
        module = stubgen.load_module_from_code(code, "<stdin>")
        lines = stubgen.stub_lines(module)
        if args.output and args.output != "-":
            stubgen.write_stub(Path(args.output), lines, command)
        else:
            _stdout_write(lines, command)
        return 0

    cwd = Path.cwd()
    for target in args.paths:
        path = Path(target)
        default_output = None
        if args.output != "-":
            default_output = _default_output_path(path, cwd, is_file=path.is_file())
        if path.is_file():
            lines = stubgen.stub_lines(stubgen.load_module_from_path(path))
            if args.output == "-":
                _stdout_write(lines, command)
            else:
                dest = Path(args.output) if args.output else default_output
                stubgen.write_stub(dest, lines, command)
        else:
            if args.output == "-":
                out_dir = None
            else:
                out_dir = Path(args.output) if args.output else default_output
            stubgen.process_directory(path, out_dir, command=command)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
