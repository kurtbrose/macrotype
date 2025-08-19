# Generated via: manual edit
# Do not edit by hand
from __future__ import annotations

from pathlib import Path
from types import ModuleType
from typing import Sequence

from macrotype.modules.ir import SourceInfo

def _header_lines(command: str | None) -> list[str]: ...
def _has_type_checking_guard(code: str) -> bool: ...
def load_module_from_path(path: Path, *, allow_type_checking: bool = ...) -> ModuleType: ...
def load_module_from_code(
    code: str, name: str = ..., *, allow_type_checking: bool = ...
) -> ModuleType: ...
def stub_lines(
    module: ModuleType,
    *,
    source_info: SourceInfo | None = ...,
    strict: bool = ...,
) -> list[str]: ...
def write_stub(dest: Path, lines: list[str], command: str | None = ...) -> None: ...
def iter_python_files(target: Path, *, skip: Sequence[str] = ...) -> list[Path]: ...
def process_file(
    src: Path,
    dest: Path | None = ...,
    *,
    command: str | None = ...,
    strict: bool = ...,
    allow_type_checking: bool = ...,
) -> Path: ...
def process_directory(
    directory: Path,
    out_dir: Path | None = ...,
    *,
    command: str | None = ...,
    strict: bool = ...,
    allow_type_checking: bool = ...,
    skip: Sequence[str] = ...,
) -> list[Path]: ...
