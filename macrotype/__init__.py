"""Utilities for extracting type information and generating stub files."""

from .pyi_extract import (
    PyiClass,
    PyiElement,
    PyiFunction,
    PyiModule,
    PyiVariable,
    TypeRenderInfo,
    find_typevars,
    format_type,
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
from .meta_types import (
    clear_registry,
    emit_as,
    get_caller_module,
    get_overloads,
    make_literal_map,
    overload,
    overload_for,
    patch_typing,
    set_module,
)
from .stubgen import (
    iter_python_files,
    load_module_from_code,
    load_module_from_path,
    process_directory,
    process_file,
    stub_lines,
    write_stub,
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
    "make_literal_map",
    "set_module",
    "get_caller_module",
    "overload",
    "overload_for",
    "get_overloads",
    "clear_registry",
    "patch_typing",
]
