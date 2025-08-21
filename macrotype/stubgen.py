from __future__ import annotations

import fnmatch
import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Sequence

from .meta_types import patch_typing
from .modules.ir import SourceInfo
from .modules.source import extract_source_info, extract_type_checking_imports


class MypyPluginError(RuntimeError):
    """Raised when a module appears to be a mypy plugin."""


_MYPY_PLUGIN_PATTERNS = (
    ".mypy.",
    ".mypy",
    "ext.mypy",
    "typing_plugin",
    "mypy_plugin",
)


def _looks_like_mypy_plugin(name: str) -> bool:
    return any(pat in name or name.endswith(pat) for pat in _MYPY_PLUGIN_PATTERNS)


def _header_lines(command: str | None) -> list[str]:
    """Return standard header lines for generated stubs."""
    if command:
        return [f"# Generated via: {command}", "# Do not edit by hand"]
    return []


def _module_name_from_path(path: Path) -> str:
    parts = [path.stem]
    parent = path.parent
    while (parent / "__init__.py").exists():
        parts.append(parent.name)
        parent = parent.parent
    return ".".join(reversed(parts))


def load_module(name: str, *, allow_type_checking: bool = False) -> ModuleType:
    spec = importlib.util.find_spec(name)
    if spec is None or spec.origin is None or not spec.origin.endswith(".py"):
        raise ImportError(f"Cannot import {name}")
    if not allow_type_checking:
        code = Path(spec.origin).read_text()
        try:
            extract_type_checking_imports(code)
        except RuntimeError as exc:
            raise RuntimeError(f"Skipped {name} due to TYPE_CHECKING guard") from exc
    try:
        with patch_typing():
            module = importlib.import_module(name)
    except (ImportError, ModuleNotFoundError) as exc:  # pragma: no cover - defensive
        msg = str(exc)
        if "mypy" in msg or "ExpandTypeVisitor" in msg:
            raise MypyPluginError(msg) from exc
        raise
    return module


def load_module_from_code(
    code: str,
    name: str = "<string>",
    *,
    allow_type_checking: bool = False,
) -> ModuleType:
    if not allow_type_checking:
        try:
            extract_type_checking_imports(code)
        except RuntimeError as exc:
            raise RuntimeError("Skipped module due to TYPE_CHECKING guard") from exc
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


def process_module(
    module: ModuleType,
    dest: Path | None = None,
    *,
    command: str | None = None,
    strict: bool = False,
    source_info: SourceInfo | None = None,
) -> Path:
    lines = stub_lines(module, source_info=source_info, strict=strict)
    if dest is None:
        file = getattr(module, "__file__", None)
        if file is None:
            raise ValueError("dest must be provided for modules without __file__")
        dest = Path(file).with_suffix(".pyi")
    write_stub(dest, lines, command)
    return dest


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
    try:
        info = extract_source_info(code, allow_type_checking=allow_type_checking)
    except RuntimeError:
        raise RuntimeError(f"Skipped {src} due to TYPE_CHECKING guard")
    module_name = _module_name_from_path(src)
    if _looks_like_mypy_plugin(module_name):
        raise MypyPluginError(f"{module_name} appears to be a mypy plugin")
    module = load_module(module_name, allow_type_checking=True)
    dest = dest or src.with_suffix(".pyi")
    return process_module(
        module,
        dest,
        command=command,
        strict=strict,
        source_info=info,
    )


def process_directory(
    directory: Path,
    out_dir: Path | None = None,
    *,
    command: str | None = None,
    strict: bool = False,
    allow_type_checking: bool = False,
    skip: Sequence[str] = (),
    debug_failure: bool = False,
) -> list[Path]:
    outputs: list[Path] = []
    for src in iter_python_files(directory, skip=skip):
        module_name = _module_name_from_path(src)
        if _looks_like_mypy_plugin(module_name):
            print(f"Skipping {src}: appears to be a mypy plugin", file=sys.stderr)
            continue
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
        except MypyPluginError as exc:
            print(f"Skipping {src}: {exc}", file=sys.stderr)
        except (Exception, SystemExit) as exc:  # pragma: no cover - defensive
            if debug_failure:
                import pdb
                import traceback

                traceback.print_exception(type(exc), exc, exc.__traceback__)
                pdb.post_mortem(exc.__traceback__)
            else:
                print(f"Skipping {src}: {exc}", file=sys.stderr)
    return outputs


__all__ = [
    "load_module",
    "load_module_from_code",
    "stub_lines",
    "write_stub",
    "process_module",
    "iter_python_files",
    "process_file",
    "process_directory",
]
