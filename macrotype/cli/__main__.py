from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .. import stubgen
from ..modules.ir import SourceInfo
from ..modules.source import extract_source_info
from . import _default_output_path
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
        "--strict",
        action="store_true",
        help="Normalize and validate annotations",
    )
    parser.add_argument(
        "--allow-type-checking",
        action="store_true",
        help="Process modules guarded by TYPE_CHECKING",
    )
    args = parser.parse_args(argv)
    command = "macrotype " + " ".join(argv)
    allow_tc = args.allow_type_checking

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
        module = stubgen.load_module_from_code(code, "<stdin>", allow_type_checking=allow_tc)
        header, comments, line_map = extract_source_info(code)
        info = SourceInfo(headers=header, comments=comments, line_map=line_map)
        lines = stubgen.stub_lines(module, source_info=info, strict=args.strict)
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
            if args.output == "-":
                code = path.read_text()
                module_name = stubgen._module_name_from_path(path)
                module = stubgen.load_module(module_name, allow_type_checking=allow_tc)
                header, comments, line_map = extract_source_info(code)
                info = SourceInfo(headers=header, comments=comments, line_map=line_map)
                lines = stubgen.stub_lines(module, source_info=info, strict=args.strict)
                _stdout_write(lines, command)
            else:
                dest = Path(args.output) if args.output else default_output
                stubgen.process_file(
                    path,
                    dest,
                    command=command,
                    strict=args.strict,
                    allow_type_checking=allow_tc,
                )
        else:
            out_dir = (
                None if args.output == "-" else Path(args.output) if args.output else default_output
            )
            stubgen.process_directory(
                path,
                out_dir,
                command=command,
                strict=args.strict,
                allow_type_checking=allow_tc,
            )
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(argv or sys.argv[1:])
    return _stub_main(argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
