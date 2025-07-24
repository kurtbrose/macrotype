"""Utilities for extracting type information and generating stub files."""

import sys
import typing

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

from .overload_support import _OVERLOAD_REGISTRY
from typing import Literal

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
]


def emit_as(name: str):
    """Decorator that overrides the emitted name for a function or class.

    When ``@overload`` definitions are executed inside the decorated object,
    they register themselves under the original qualified name.  This helper
    moves those registrations so that lookups by the emitted name succeed.
    """

    def set_qualname(obj):
        obj.__qualname_override__ = name

        mod_overloads = _OVERLOAD_REGISTRY.get(obj.__module__)
        if mod_overloads:
            old_prefix = obj.__qualname__ + "."
            new_prefix = name + "."
            for key in list(mod_overloads.keys()):
                if key.startswith(old_prefix):
                    funcs = mod_overloads.pop(key)
                    new_key = new_prefix + key[len(old_prefix):]
                    mod_overloads[new_key] = funcs
                    method_name = key[len(old_prefix):].split(".", 1)[0]
                    attr = getattr(obj, method_name, None)
                    if callable(attr):
                        setattr(attr, "__overload_name__", new_key)
                    for ov in funcs:
                        setattr(ov, "__overload_name__", new_key)

        return obj

    return set_qualname


def make_literal_map(name: str, mapping: dict[str | int, str | int]):
    """Dynamically build a class exposing ``mapping`` via ``Literal`` overloads."""

    caller_mod = sys._getframe(1).f_globals.get("__name__", "__main__")

    @emit_as(name)
    class LiteralMap:
        for k, v in mapping.items():
            @typing.overload  # type: ignore[misc]
            def __getitem__(self, key: Literal[k]) -> Literal[v]: ...

        def __getitem__(self, key):
            return mapping[key]

    old_mod = LiteralMap.__module__
    LiteralMap.__module__ = caller_mod
    for attr_name, attr in list(LiteralMap.__dict__.items()):
        if callable(attr):
            attr.__module__ = caller_mod

    if old_mod != caller_mod:
        old_overloads = _OVERLOAD_REGISTRY.get(old_mod)
        if old_overloads:
            for key in list(old_overloads.keys()):
                if key.startswith(name + "."):
                    _OVERLOAD_REGISTRY[caller_mod][key] = old_overloads.pop(key)

    return LiteralMap
