from __future__ import annotations

import ast
import fnmatch
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


def _module_name_and_packages(path: Path) -> tuple[str, list[tuple[str, Path]]]:
    parts = [path.stem]
    pkg_dirs: list[Path] = []
    parent = path.parent
    while (parent / "__init__.py").exists():
        parts.append(parent.name)
        pkg_dirs.append(parent)
        parent = parent.parent
    module_name = ".".join(reversed(parts))
    package_parts = list(reversed(parts[1:]))
    pkg_dirs = list(reversed(pkg_dirs))
    packages: list[tuple[str, Path]] = []
    acc: list[str] = []
    for part, dir in zip(package_parts, pkg_dirs):
        acc.append(part)
        packages.append((".".join(acc), dir))
    return module_name, packages


def load_module_from_path(path: Path, *, allow_type_checking: bool = False) -> ModuleType:
    code = path.read_text()
    if not allow_type_checking and _has_type_checking_guard(code):
        raise RuntimeError(f"Skipped {path} due to TYPE_CHECKING guard")
    module_name, packages = _module_name_and_packages(path)
    existing_module = sys.modules.get(module_name)
    pre_modules = set(sys.modules)
    for pkg_name, pkg_dir in packages:
        if pkg_name not in sys.modules:
            pkg = ModuleType(pkg_name)
            pkg.__path__ = [str(pkg_dir)]  # type: ignore[attr-defined]
            sys.modules[pkg_name] = pkg
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    module.__package__ = module_name.rpartition(".")[0]
    sys.modules[module_name] = module
    with patch_typing():
        spec.loader.exec_module(module)
    added = set(sys.modules) - pre_modules

    def _cleanup() -> None:
        if existing_module is not None:
            sys.modules[module_name] = existing_module
        else:
            sys.modules.pop(module_name, None)
        for name in added - {module_name}:
            sys.modules.pop(name, None)

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
    module = load_module_from_path(src, allow_type_checking=allow_type_checking)
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
    "load_module_from_path",
    "load_module_from_code",
    "stub_lines",
    "write_stub",
    "iter_python_files",
    "process_file",
    "process_directory",
]
