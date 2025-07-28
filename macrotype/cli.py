from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import stubgen


def _stdout_write(lines: list[str], command: str | None = None) -> None:
    sys.stdout.write("\n".join(stubgen._header_lines(command) + lines) + "\n")


def main(argv: list[str] | None = None) -> int:
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
    args = parser.parse_args(argv)
    command = "macrotype " + " ".join(argv or sys.argv[1:])

    if args.paths == ["-"]:
        code = sys.stdin.read()
        module = stubgen.load_module_from_code(code, "<stdin>")
        lines = stubgen.stub_lines(module)
        if args.output and args.output != "-":
            stubgen.write_stub(Path(args.output), lines, command)
        else:
            _stdout_write(lines, command)
        return 0

    for target in args.paths:
        path = Path(target)
        if path.is_file():
            lines = stubgen.stub_lines(stubgen.load_module_from_path(path))
            if args.output == "-":
                _stdout_write(lines, command)
            else:
                dest = Path(args.output) if args.output else path.with_suffix(".pyi")
                stubgen.write_stub(dest, lines, command)
        else:
            out_dir = Path(args.output) if args.output and args.output != "-" else None
            stubgen.process_directory(path, out_dir, command=command)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
