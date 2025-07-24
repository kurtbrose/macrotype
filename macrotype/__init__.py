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

from .meta_types import (
    emit_as,
    make_literal_map,
    set_module,
    get_caller_module,
    overload,
    get_overloads,
    clear_registry,
    patch_typing,
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
    "get_overloads",
    "clear_registry",
    "patch_typing",
]
