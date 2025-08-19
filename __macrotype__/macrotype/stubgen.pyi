# Generated via: macrotype macrotype/stubgen.py -o __macrotype__/macrotype/stubgen.pyi
# Do not edit by hand
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from types import ModuleType

from macrotype.modules.ir import SourceInfo

annotations = annotations

def _header_lines(command: None | str) -> list[str]: ...
def _has_type_checking_guard(code: str) -> bool: ...
def _module_name_from_path(path: Path) -> str: ...
def load_module(name: str, allow_type_checking: bool) -> ModuleType: ...
def load_module_from_code(code: str, name: str, allow_type_checking: bool) -> ModuleType: ...
def stub_lines(module: ModuleType, source_info: None | SourceInfo, strict: bool) -> list[str]: ...
def write_stub(dest: Path, lines: list[str], command: None | str) -> None: ...
def process_module(
    module: ModuleType,
    dest: None | Path,
    command: None | str,
    strict: bool,
    source_info: None | SourceInfo,
) -> Path: ...
def iter_python_files(target: Path, skip: Sequence[str]) -> list[Path]: ...
def process_file(
    src: Path, dest: None | Path, command: None | str, strict: bool, allow_type_checking: bool
) -> Path: ...
def process_directory(
    directory: Path,
    out_dir: None | Path,
    command: None | str,
    strict: bool,
    allow_type_checking: bool,
    skip: Sequence[str],
) -> list[Path]: ...
