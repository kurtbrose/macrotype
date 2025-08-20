# Generated via: macrotype macrotype
# Do not edit by hand
from typing import Any, Callable, get_overloads, overload

# Re-export ``typing.overload`` and ``typing.get_overloads`` so type checkers
# recognize them as the standard overload helpers.
_OVERLOAD_REGISTRY: dict[str, dict[str, list[Callable]]]

_ORIG_GET_OVERLOADS = get_overloads

_ORIG_OVERLOAD = overload
__all__ = [
    "emit_as",
    "set_module",
    "get_caller_module",
    "make_literal_map",
    "overload",
    "overload_for",
    "get_overloads",
    "clear_registry",
    "patch_typing",
    "all_annotations",
]

def overload_for(*args, **kwargs): ...
def clear_registry() -> None: ...
def patch_typing(): ...
def get_caller_module(level: int) -> str: ...
def set_module(obj: Any, module: str) -> None: ...
def emit_as(name: str): ...
def make_literal_map(name: str, mapping: dict[int | str, int | str]): ...
def all_annotations(cls: type) -> dict[str, Any]: ...
