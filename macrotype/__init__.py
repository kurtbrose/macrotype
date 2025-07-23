"""Utilities for extracting type information and generating stub files."""

from .pyi_extract import (
    PyiElement,
    TypeRenderInfo,
    PyiVariable,
    PyiFunction,
    PyiClass,
    PyiModule,
    format_type,
    find_typevars,
)

__all__ = [
    "PyiElement",
    "TypeRenderInfo",
    "PyiVariable",
    "PyiFunction",
    "PyiClass",
    "PyiModule",
    "format_type",
    "find_typevars",
]
from .stubgen import (
    load_module_from_path,
    load_module_from_code,
    stub_lines,
    write_stub,
    iter_python_files,
    process_file,
    process_directory,
)

__all__ += [
    "load_module_from_path",
    "load_module_from_code",
    "stub_lines",
    "write_stub",
    "iter_python_files",
    "process_file",
    "process_directory",
    "emit_as",
]


def emit_as(name: str):
    """Decorator that overrides the emitted name for a function or class."""

    def set_qualname(obj):
        obj.__qualname_override__ = name
        return obj

    return set_qualname
