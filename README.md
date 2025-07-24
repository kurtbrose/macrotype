# Macrotype

`macrotype` is a small library that helps generate stub (`.pyi`) files from
existing Python modules. It has no dependencies and works with modern versions
of Python.

This enables dynamically generated `__annotations__` in python classes and functions, which would otherwise be invisible to python type checkers, to work.  Any arbitrary code can run at import time to create `__annotations__`.  As an example of the power of this approach out of the box, it provides an alternative to dataclass_transform.

Basically, this is a little hack to get type macros in python.

## Current Functionality

- Generate `.pyi` stub files from existing modules
- Helpers like `emit_as` and `make_literal_map` for dynamic overloads
