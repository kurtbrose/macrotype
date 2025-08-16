"""Public entrypoints for macrotype."""

from types import ModuleType

from .modules import from_module

__all__ = ["from_module", "ModuleType"]
