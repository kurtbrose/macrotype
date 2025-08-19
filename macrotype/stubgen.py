from __future__ import annotations

import ast
import fnmatch
import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Sequence

from .meta_types import patch_typing
from .modules.ir import SourceInfo
from .modules.source import extract_source_info


def _header_lines(command: str | None) -> list[str]:
    """Return standard header lines for generated stubs."""
    if command:
        return [f"# Generated via: {command}", "# Do not edit by hand"]
    return []


def _has_type_checking_guard(code: str) -> bool:
    tree = ast.parse(code)

    def mentions_TYPE_CHECKING(expr: ast.AST) -> bool:
        if isinstance(expr, ast.Name) and expr.id == "TYPE_CHECKING":
            return True
        if (
            isinstance(expr, ast.Attribute)
            and isinstance(expr.value, ast.Name)
            and expr.value.id == "typing"
            and expr.attr == "TYPE_CHECKING"
        ):
            return True
        return any(mentions_TYPE_CHECKING(c) for c in ast.iter_child_nodes(expr))

    for node in ast.walk(tree):
        if isinstance(node, ast.If) and mentions_TYPE_CHECKING(node.test):
            return True
    return False


def _module_name_from_path(path: Path) -> str:
    parts = [path.stem]
    parent = path.parent
    while (parent / "__init__.py").exists():
        parts.append(parent.name)
        parent = parent.parent
    return ".".join(reversed(parts))


def load_module(name: str, *, allow_type_checking: bool = False) -> ModuleType:
    pre_modules = set(sys.modules)
    spec = importlib.util.find_spec(name)
    if spec is None or spec.origin is None or not spec.origin.endswith(".py"):
        raise ImportError(f"Cannot import {name}")
    if not allow_type_checking:
        code = Path(spec.origin).read_text()
        if _has_type_checking_guard(code):
            raise RuntimeError(f"Skipped {name} due to TYPE_CHECKING guard")
    existing_module = sys.modules.get(name)
    with patch_typing():
        module = importlib.import_module(name)
    added = set(sys.modules) - pre_modules

    def _cleanup() -> None:
        if existing_module is not None:
            sys.modules[name] = existing_module
        else:
            sys.modules.pop(name, None)
        for mod_name in added - {name}:
            sys.modules.pop(mod_name, None)

    module.__dict__["__cleanup__"] = _cleanup
    return module


def load_module_from_code(
    code: str,
    name: str = "<string>",
    *,
    allow_type_checking: bool = False,
) -> ModuleType:
    if not allow_type_checking and _has_type_checking_guard(code):
        raise RuntimeError("Skipped module due to TYPE_CHECKING guard")
    module = ModuleType(name)
    sys.modules[name] = module
    with patch_typing():
        exec(compile(code, name, "exec"), module.__dict__)
    return module


def stub_lines(
    module: ModuleType,
    *,
    source_info: SourceInfo | None = None,
    strict: bool = False,
) -> list[str]:
    from . import modules

    mi = modules.from_module(module, source_info=source_info, strict=strict)
    return modules.emit_module(mi)


def write_stub(dest: Path, lines: list[str], command: str | None = None) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(_header_lines(command) + list(lines)) + "\n")


def iter_python_files(target: Path, *, skip: Sequence[str] = ()) -> list[Path]:
    if target.is_file():
        return [target]
    files: list[Path] = []
    for p in target.rglob("*.py"):
        rel = p.relative_to(target)
        if any(fnmatch.fnmatch(str(rel), pattern) for pattern in skip):
            continue
        files.append(p)
    return files


def process_file(
    src: Path,
    dest: Path | None = None,
    *,
    command: str | None = None,
    strict: bool = False,
    allow_type_checking: bool = False,
) -> Path:
    code = src.read_text()
    if not allow_type_checking and _has_type_checking_guard(code):
        raise RuntimeError(f"Skipped {src} due to TYPE_CHECKING guard")
    module_name = _module_name_from_path(src)
    module = load_module(module_name, allow_type_checking=True)
    header, comments, line_map = extract_source_info(code)
    info = SourceInfo(headers=header, comments=comments, line_map=line_map)
    lines = stub_lines(module, source_info=info, strict=strict)
    dest = dest or src.with_suffix(".pyi")
    write_stub(dest, lines, command)
    return dest


def process_directory(
    directory: Path,
    out_dir: Path | None = None,
    *,
    command: str | None = None,
    strict: bool = False,
    allow_type_checking: bool = False,
    skip: Sequence[str] = (),
) -> list[Path]:
    outputs: list[Path] = []
    for src in iter_python_files(directory, skip=skip):
        if out_dir:
            rel = src.relative_to(directory).with_suffix(".pyi")
            dest = out_dir / rel
        else:
            dest = None
        try:
            outputs.append(
                process_file(
                    src,
                    dest,
                    command=command,
                    strict=strict,
                    allow_type_checking=allow_type_checking,
                )
            )
        except (Exception, SystemExit) as exc:  # pragma: no cover - defensive
            print(f"Skipping {src}: {exc}", file=sys.stderr)
    return outputs


__all__ = [
    "load_module",
    "load_module_from_code",
    "stub_lines",
    "write_stub",
    "iter_python_files",
    "process_file",
    "process_directory",
]
