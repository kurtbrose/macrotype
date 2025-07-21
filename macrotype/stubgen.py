from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

from .pyi_extract import PyiModule


def load_module_from_path(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


def load_module_from_code(code: str, name: str = "<string>") -> ModuleType:
    module = ModuleType(name)
    exec(compile(code, name, "exec"), module.__dict__)
    return module


def stub_lines(module: ModuleType) -> list[str]:
    return PyiModule.from_module(module).render()


def write_stub(dest: Path, lines: list[str]) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(lines) + "\n")


def iter_python_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    return list(target.rglob("*.py"))


def process_file(src: Path, dest: Path | None = None) -> Path:
    module = load_module_from_path(src)
    lines = stub_lines(module)
    dest = dest or src.with_suffix(".pyi")
    write_stub(dest, lines)
    return dest


def process_directory(directory: Path, out_dir: Path | None = None) -> list[Path]:
    outputs = []
    for src in iter_python_files(directory):
        dest = (out_dir / src.with_suffix(".pyi").name) if out_dir else None
        outputs.append(process_file(src, dest))
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
