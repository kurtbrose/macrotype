from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .. import stubgen
from . import DEFAULT_OUT_DIR, _default_output_path
from .watch import watch_and_run


def _stdout_write(lines: list[str], command: str | None = None) -> None:
    sys.stdout.write("\n".join(stubgen._header_lines(command) + lines) + "\n")


def _stub_main(argv: list[str]) -> int:
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
    parser.add_argument(
        "--stub-overlay-dir",
        help="Symlink generated stubs into this directory for type checkers",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Normalize and validate annotations",
    )
    args = parser.parse_args(argv)
    command = "macrotype " + " ".join(argv)
    stub_overlay_dir = Path(args.stub_overlay_dir) if args.stub_overlay_dir else None

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
        if stub_overlay_dir:
            parser.error("--stub-overlay-dir cannot be used with stdin")
        code = sys.stdin.read()
        module = stubgen.load_module_from_code(code, "<stdin>")
        lines = stubgen.stub_lines(module, strict=args.strict)
        if args.output and args.output != "-":
            stubgen.write_stub(Path(args.output), lines, command)
        else:
            _stdout_write(lines, command)
        return 0

    cwd = Path.cwd()
    for target in args.paths:
        path = Path(target)
        default_output = None
        if args.output is None:
            default_output = _default_output_path(path, cwd, is_file=path.is_file())
        if path.is_file():
            if args.output == "-":
                if stub_overlay_dir:
                    parser.error("--stub-overlay-dir requires a file output")
                lines = stubgen.stub_lines(
                    stubgen.load_module_from_path(path),
                    strict=args.strict,
                )
                _stdout_write(lines, command)
            else:
                dest = Path(args.output) if args.output else default_output
                overlay = stub_overlay_dir
                if overlay is None and dest.parent != path.parent:
                    overlay = (
                        DEFAULT_OUT_DIR if dest.is_relative_to(DEFAULT_OUT_DIR) else dest.parent
                    )
                stubgen.process_file(
                    path,
                    dest,
                    command=command,
                    stub_overlay_dir=overlay,
                    strict=args.strict,
                )
        else:
            if args.output == "-":
                if stub_overlay_dir:
                    parser.error("--stub-overlay-dir requires a directory output")
                out_dir = None
                overlay = None
            else:
                out_dir = Path(args.output) if args.output else default_output
                overlay = stub_overlay_dir
                if overlay is None and out_dir and out_dir != path:
                    overlay = (
                        DEFAULT_OUT_DIR if out_dir.is_relative_to(DEFAULT_OUT_DIR) else out_dir
                    )
            stubgen.process_directory(
                path,
                out_dir,
                command=command,
                stub_overlay_dir=overlay,
                strict=args.strict,
            )
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(argv or sys.argv[1:])
    return _stub_main(argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
